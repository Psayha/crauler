"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "@/components/providers/TelegramProvider";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/websocket";
import { useQuery } from "@tanstack/react-query";
import { ProjectCard } from "@/components/ProjectCard";
import { StatsCard } from "@/components/StatsCard";
import { Loader2, Plus, Zap, CheckCircle2, Clock } from "lucide-react";

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
          setIsAuthenticated(false);
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

  return (
    <div className="min-h-screen pb-24">
      {/* Header */}
      <div className="bg-tg-secondary-bg p-4 sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">
              Привет, {currentUser?.first_name || user?.first_name || "пользователь"}!
            </h1>
            <p className="text-sm text-tg-hint">
              Кредиты: {currentUser?.credits_balance || 100}
            </p>
          </div>
          <div className="w-12 h-12 bg-tg-button rounded-full flex items-center justify-center text-2xl">
            👤
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 p-4">
        <StatsCard
          icon={<Zap className="w-5 h-5" />}
          label="Активных"
          value={activeProjects.length}
          color="text-yellow-500"
        />
        <StatsCard
          icon={<CheckCircle2 className="w-5 h-5" />}
          label="Завершено"
          value={completedProjects.length}
          color="text-green-500"
        />
        <StatsCard
          icon={<Clock className="w-5 h-5" />}
          label="Всего"
          value={projects?.length || 0}
          color="text-blue-500"
        />
      </div>

      {/* Projects */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Проекты</h2>
          <button
            onClick={() => router.push("/projects")}
            className="text-sm text-tg-link"
          >
            Все проекты →
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
          <div className="text-center py-12">
            <div className="text-5xl mb-4">📋</div>
            <p className="text-tg-hint mb-4">У вас пока нет проектов</p>
            <button
              onClick={() => router.push("/projects/new")}
              className="inline-flex items-center gap-2 px-4 py-2 bg-tg-button text-tg-button-text rounded-lg"
            >
              <Plus className="w-4 h-4" />
              Создать первый проект
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
