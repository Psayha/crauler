"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTelegram } from "@/components/providers/TelegramProvider";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/websocket";
import { TaskTree } from "@/components/TaskTree";
import { getStatusColor, getStatusLabel, formatRelativeTime, formatNumber } from "@/lib/utils";
import {
  Loader2,
  Play,
  CheckCircle2,
  Clock,
  AlertCircle,
  Users,
  Zap,
  Calendar,
  TrendingUp,
  List,
  Network,
} from "lucide-react";

export default function ProjectDetailsPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;
  const { webApp } = useTelegram();
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<"list" | "tree">("list");

  // Fetch project
  const { data: project, isLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId),
  });

  // Fetch tasks
  const { data: tasks } = useQuery({
    queryKey: ["tasks", projectId],
    queryFn: () => api.getProjectTasks(projectId),
    enabled: !!project,
  });

  // Fetch progress
  const { data: progress } = useQuery({
    queryKey: ["progress", projectId],
    queryFn: () => api.getProjectProgress(projectId),
    enabled: !!project && project.status === "in_progress",
    refetchInterval: 5000, // Poll every 5s when in progress
  });

  // Execute project mutation
  const executeProject = useMutation({
    mutationFn: () => api.executeProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["tasks", projectId] });
    },
  });

  // Setup WebSocket subscriptions
  useEffect(() => {
    if (projectId) {
      wsClient.subscribeToProject(projectId);

      const handleProjectUpdate = (data: any) => {
        queryClient.invalidateQueries({ queryKey: ["project", projectId] });
        queryClient.invalidateQueries({ queryKey: ["progress", projectId] });
      };

      const handleTaskUpdate = (data: any) => {
        queryClient.invalidateQueries({ queryKey: ["tasks", projectId] });
      };

      wsClient.on("project_update", handleProjectUpdate);
      wsClient.on("task_update", handleTaskUpdate);

      return () => {
        wsClient.unsubscribeFromProject(projectId);
        wsClient.off("project_update", handleProjectUpdate);
        wsClient.off("task_update", handleTaskUpdate);
      };
    }
  }, [projectId, queryClient]);

  // Setup Telegram buttons
  useEffect(() => {
    if (webApp) {
      webApp.BackButton.show();
      webApp.BackButton.onClick(() => {
        router.back();
      });

      if (project && (project.status === "draft" || project.status === "planning")) {
        webApp.MainButton.text = "🚀 Запустить проект";
        webApp.MainButton.show();
        webApp.MainButton.onClick(() => {
          webApp.showConfirm("Запустить выполнение проекта AI агентами?", (confirmed) => {
            if (confirmed) {
              executeProject.mutate();
            }
          });
        });
      } else {
        webApp.MainButton.hide();
      }

      return () => {
        webApp.BackButton.hide();
        webApp.MainButton.hide();
      };
    }
  }, [webApp, router, project, executeProject]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-tg-link" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4 text-center">
        <div className="text-5xl mb-4">❌</div>
        <p className="text-tg-hint">Проект не найден</p>
      </div>
    );
  }

  const getProjectIcon = (type: string) => {
    const icons: Record<string, string> = {
      website: "🌐",
      mobile_app: "📱",
      marketing_campaign: "📊",
      data_analysis: "📈",
      content_creation: "✍️",
      custom: "⚙️",
    };
    return icons[type] || "📋";
  };

  const tasksByStatus = {
    pending: tasks?.filter((t: any) => t.status === "pending") || [],
    in_progress: tasks?.filter((t: any) => t.status === "in_progress") || [],
    completed: tasks?.filter((t: any) => t.status === "completed") || [],
    failed: tasks?.filter((t: any) => t.status === "failed") || [],
  };

  const totalTasks = tasks?.length || 0;
  const completedTasks = tasksByStatus.completed.length;
  const progressPercent = progress?.progress || (totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0);

  // Get unique agents
  const agents = tasks?.reduce((acc: string[], task: any) => {
    if (task.assigned_agent && !acc.includes(task.assigned_agent)) {
      acc.push(task.assigned_agent);
    }
    return acc;
  }, []) || [];

  return (
    <div className="min-h-screen pb-24 bg-tg-bg">
      {/* Header */}
      <div className="bg-gradient-to-br from-tg-button/10 to-purple-500/10 p-6 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-start gap-4 mb-4">
          <div className="w-14 h-14 bg-gradient-to-br from-tg-button to-purple-500 rounded-2xl flex items-center justify-center text-3xl shadow-lg">
            {getProjectIcon(project.type)}
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-bold mb-1">{project.name}</h1>
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                  project.status
                )} bg-opacity-20`}
              >
                {getStatusLabel(project.status)}
              </span>
              {project.priority && project.priority !== "normal" && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400">
                  {project.priority === "high" ? "🔥 Высокий" : "⚡ Критичный"}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-4 h-4 text-blue-500" />
              <span className="text-xs text-tg-hint">Задач</span>
            </div>
            <p className="text-2xl font-bold">{totalTasks}</p>
            <p className="text-xs text-tg-hint">{completedTasks} завершено</p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-1">
              <Users className="w-4 h-4 text-purple-500" />
              <span className="text-xs text-tg-hint">Агенты</span>
            </div>
            <p className="text-2xl font-bold">{agents.length}</p>
            <p className="text-xs text-tg-hint">работают над проектом</p>
          </div>
        </div>

        {/* Progress Bar */}
        {totalTasks > 0 && (
          <div>
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-tg-hint font-medium">Прогресс</span>
              <span className="font-bold">{progressPercent}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-tg-button to-purple-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Description */}
      {project.description && (
        <div className="p-4">
          <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-tg-link" />
            Описание
          </h3>
          <p className="text-sm bg-tg-secondary-bg rounded-xl p-4 leading-relaxed">
            {project.description}
          </p>
        </div>
      )}

      {/* Task Stats */}
      {tasks && tasks.length > 0 && (
        <div className="px-4 pb-4">
          <div className="grid grid-cols-4 gap-2">
            <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-3 text-center">
              <Clock className="w-5 h-5 mx-auto mb-1 text-gray-500" />
              <div className="text-lg font-bold">{tasksByStatus.pending.length}</div>
              <div className="text-xs text-tg-hint">Ожидание</div>
            </div>
            <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-3 text-center">
              <Loader2 className="w-5 h-5 mx-auto mb-1 text-yellow-500" />
              <div className="text-lg font-bold text-yellow-700 dark:text-yellow-300">
                {tasksByStatus.in_progress.length}
              </div>
              <div className="text-xs text-yellow-600 dark:text-yellow-400">В работе</div>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-3 text-center">
              <CheckCircle2 className="w-5 h-5 mx-auto mb-1 text-green-500" />
              <div className="text-lg font-bold text-green-700 dark:text-green-300">
                {tasksByStatus.completed.length}
              </div>
              <div className="text-xs text-green-600 dark:text-green-400">Готово</div>
            </div>
            <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-3 text-center">
              <AlertCircle className="w-5 h-5 mx-auto mb-1 text-red-500" />
              <div className="text-lg font-bold text-red-700 dark:text-red-300">
                {tasksByStatus.failed.length}
              </div>
              <div className="text-xs text-red-600 dark:text-red-400">Ошибки</div>
            </div>
          </div>
        </div>
      )}

      {/* View Mode Toggle */}
      {tasks && tasks.length > 0 && (
        <div className="px-4 pb-3">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">Задачи</h3>
            <div className="flex items-center gap-1 bg-tg-secondary-bg rounded-lg p-1">
              <button
                onClick={() => setViewMode("list")}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  viewMode === "list"
                    ? "bg-tg-button text-tg-button-text"
                    : "text-tg-hint"
                }`}
              >
                <List className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode("tree")}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  viewMode === "tree"
                    ? "bg-tg-button text-tg-button-text"
                    : "text-tg-hint"
                }`}
              >
                <Network className="w-4 h-4" />
              </button>
            </div>
          </div>

          {viewMode === "tree" ? (
            <TaskTree tasks={tasks} />
          ) : (
            <div className="space-y-2">
              {tasks.map((task: any) => (
                <div
                  key={task.id}
                  className="bg-tg-secondary-bg rounded-xl p-4"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h4 className="font-medium text-sm mb-1">{task.title}</h4>
                      {task.assigned_agent && (
                        <div className="flex items-center gap-1 text-xs text-tg-hint">
                          <Users className="w-3 h-3" />
                          <span>{task.assigned_agent}</span>
                        </div>
                      )}
                    </div>
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(
                        task.status
                      )} bg-opacity-20 flex-shrink-0`}
                    >
                      {getStatusLabel(task.status)}
                    </span>
                  </div>
                  {task.description && (
                    <p className="text-xs text-tg-hint line-clamp-2">
                      {task.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Loading overlay */}
      {executeProject.isPending && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-tg-secondary-bg rounded-2xl p-8 flex flex-col items-center gap-4 shadow-2xl">
            <div className="relative">
              <Loader2 className="w-12 h-12 animate-spin text-tg-button" />
              <div className="absolute inset-0 blur-xl bg-tg-button opacity-50 animate-pulse" />
            </div>
            <p className="text-base font-medium">Запускаем AI агентов...</p>
            <p className="text-xs text-tg-hint">Это может занять несколько секунд</p>
          </div>
        </div>
      )}
    </div>
  );
}
