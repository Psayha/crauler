"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "@/components/providers/TelegramProvider";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/websocket";
import { useQuery } from "@tanstack/react-query";
import { ProjectCard } from "@/components/ProjectCard";
import { StatsCard } from "@/components/StatsCard";
import { QuickActions } from "@/components/QuickActions";
import { ActivityFeed } from "@/components/ActivityFeed";
import { AgentStatusBadge } from "@/components/AgentStatusBadge";
import {
  Loader2,
  Zap,
  CheckCircle2,
  Clock,
  TrendingUp,
  Users,
  Brain
} from "lucide-react";
import { formatCompact } from "@/lib/utils";

export default function Dashboard() {
  const { webApp, user, isReady } = useTelegram();
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState(true);

  // Authenticate with Telegram
  useEffect(() => {
    const authenticate = async () => {
      if (!isReady) return;

      try {
        // Check if already authenticated
        const token = api.getToken();
        if (token) {
          setIsAuthenticated(true);
          setIsAuthenticating(false);

          // Connect WebSocket
          wsClient.connect(token);
          return;
        }

        // Authenticate with Telegram
        if (webApp?.initData) {
          const authData = await api.authenticateTelegram(webApp.initData);
          setIsAuthenticated(true);

          // Connect WebSocket
          wsClient.connect(authData.access_token);
        } else {
          // Development mode
          console.warn("No Telegram initData, skipping authentication");
          setIsAuthenticated(true); // For development
        }
      } catch (error) {
        console.error("Authentication error:", error);
        setIsAuthenticated(false);
      } finally {
        setIsAuthenticating(false);
      }
    };

    authenticate();
  }, [isReady, webApp]);

  // Fetch projects
  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.getProjects(),
    enabled: isAuthenticated,
  });

  // Fetch current user
  const { data: currentUser } = useQuery({
    queryKey: ["user"],
    queryFn: () => api.getCurrentUser(),
    enabled: isAuthenticated,
  });

  // Fetch agents status (mock data for now)
  const { data: agentsStatus } = useQuery({
    queryKey: ["agents-status"],
    queryFn: async () => {
      // Mock data - replace with actual API call
      return {
        total: 11,
        active: 3,
        idle: 8,
      };
    },
    enabled: isAuthenticated,
  });

  // Setup Telegram MainButton
  useEffect(() => {
    if (webApp && isAuthenticated) {
      webApp.MainButton.text = "Создать проект";
      webApp.MainButton.show();
      webApp.MainButton.onClick(() => {
        router.push("/projects/new");
      });

      return () => {
        webApp.MainButton.hide();
      };
    }
  }, [webApp, isAuthenticated, router]);

  if (isAuthenticating) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-tg-link" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4 text-center">
        <div className="text-6xl mb-4">🤖</div>
        <h1 className="text-2xl font-bold mb-2">AI Agency</h1>
        <p className="text-tg-hint">
          Откройте это приложение через Telegram Mini App
        </p>
      </div>
    );
  }

  const activeProjects = projects?.filter((p: any) => p.status === "in_progress") || [];
  const completedProjects = projects?.filter((p: any) => p.status === "completed") || [];
  const totalTasks = projects?.reduce((acc: number, p: any) => acc + (p.tasks_count || 0), 0) || 0;
  const completedTasks = projects?.reduce((acc: number, p: any) => acc + (p.completed_tasks_count || 0), 0) || 0;

  // Mock activity data - replace with actual API call
  const recentActivities = projects?.slice(0, 5).map((p: any) => ({
    id: p.id,
    type: p.status === "completed" ? "project_completed" : "project_created",
    title: p.name,
    description: `Проект ${p.status === "completed" ? "завершён" : "создан"}`,
    timestamp: p.created_at || p.updated_at,
    project_id: p.id,
  })) || [];

  return (
    <div className="min-h-screen pb-24 bg-tg-bg">
      {/* Header */}
      <div className="bg-gradient-to-br from-tg-button/10 to-tg-secondary-bg p-6 sticky top-0 z-10 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <span className="text-2xl">👋</span>
              {currentUser?.first_name || user?.first_name || "Пользователь"}
            </h1>
            <p className="text-sm text-tg-hint mt-1">
              💰 {formatCompact(currentUser?.credits_balance || 100)} кредитов
            </p>
          </div>
          <div className="w-14 h-14 bg-gradient-to-br from-tg-button to-tg-link rounded-full flex items-center justify-center text-3xl shadow-lg">
            {currentUser?.first_name?.[0] || user?.first_name?.[0] || "👤"}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-4">
        <QuickActions />
      </div>

      {/* Main Stats */}
      <div className="px-4 pb-4">
        <h2 className="text-base font-semibold mb-3 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-tg-link" />
          Статистика
        </h2>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 p-4 rounded-xl border border-yellow-200 dark:border-yellow-800">
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
              <span className="text-xs font-medium text-yellow-700 dark:text-yellow-300">
                Активные
              </span>
            </div>
            <p className="text-3xl font-bold text-yellow-900 dark:text-yellow-100">
              {activeProjects.length}
            </p>
            <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">
              {activeProjects.length > 0 ? "проектов в работе" : "нет активных"}
            </p>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 p-4 rounded-xl border border-green-200 dark:border-green-800">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
              <span className="text-xs font-medium text-green-700 dark:text-green-300">
                Завершено
              </span>
            </div>
            <p className="text-3xl font-bold text-green-900 dark:text-green-100">
              {completedProjects.length}
            </p>
            <p className="text-xs text-green-600 dark:text-green-400 mt-1">
              проектов готово
            </p>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 p-4 rounded-xl border border-blue-200 dark:border-blue-800">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <span className="text-xs font-medium text-blue-700 dark:text-blue-300">
                Задачи
              </span>
            </div>
            <p className="text-3xl font-bold text-blue-900 dark:text-blue-100">
              {completedTasks}/{totalTasks}
            </p>
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
              выполнено задач
            </p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 p-4 rounded-xl border border-purple-200 dark:border-purple-800">
            <div className="flex items-center gap-2 mb-1">
              <Users className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              <span className="text-xs font-medium text-purple-700 dark:text-purple-300">
                Агенты
              </span>
            </div>
            <p className="text-3xl font-bold text-purple-900 dark:text-purple-100">
              {agentsStatus?.active || 0}/{agentsStatus?.total || 11}
            </p>
            <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
              агентов активно
            </p>
          </div>
        </div>
      </div>

      {/* Projects */}
      <div className="px-4 pb-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold flex items-center gap-2">
            <Brain className="w-5 h-5 text-tg-link" />
            Проекты
          </h2>
          <button
            onClick={() => router.push("/projects")}
            className="text-sm text-tg-link font-medium"
          >
            Все →
          </button>
        </div>

        {projectsLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-tg-hint" />
          </div>
        ) : projects && projects.length > 0 ? (
          <div className="space-y-3">
            {projects.slice(0, 5).map((project: any) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-tg-secondary-bg rounded-xl">
            <div className="text-5xl mb-4">📋</div>
            <p className="text-tg-hint mb-4">У вас пока нет проектов</p>
            <button
              onClick={() => router.push("/projects/new")}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-tg-button text-tg-button-text rounded-lg font-medium hover:opacity-90 transition-opacity"
            >
              Создать первый проект
            </button>
          </div>
        )}
      </div>

      {/* Recent Activity */}
      <div className="px-4 pb-6">
        <h2 className="text-base font-semibold mb-3">Последняя активность</h2>
        <ActivityFeed activities={recentActivities} isLoading={projectsLoading} />
      </div>
    </div>
  );
}
