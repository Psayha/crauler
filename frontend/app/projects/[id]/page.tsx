"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTelegram } from "@/components/providers/TelegramProvider";
import { api } from "@/lib/api";
import { wsClient } from "@/lib/websocket";
import { getStatusColor, getStatusLabel, formatRelativeTime } from "@/lib/utils";
import { Loader2, Play, CheckCircle2, Clock, AlertCircle, Users } from "lucide-react";

export default function ProjectDetailsPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;
  const { webApp } = useTelegram();
  const queryClient = useQueryClient();

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

      // Listen for project updates
      const handleProjectUpdate = (data: any) => {
        queryClient.invalidateQueries({ queryKey: ["project", projectId] });
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

      // Show execute button if project is in draft/planning
      if (project && (project.status === "draft" || project.status === "planning")) {
        webApp.MainButton.text = "Запустить проект";
        webApp.MainButton.show();
        webApp.MainButton.onClick(() => {
          webApp.showConfirm(
            "Запустить выполнение проекта AI агентами?",
            (confirmed) => {
              if (confirmed) {
                executeProject.mutate();
              }
            }
          );
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
  const progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  return (
    <div className="min-h-screen pb-24">
      {/* Header */}
      <div className="bg-tg-secondary-bg p-4">
        <div className="flex items-start gap-3 mb-4">
          <span className="text-4xl">{getProjectIcon(project.type)}</span>
          <div className="flex-1">
            <h1 className="text-xl font-bold mb-1">{project.name}</h1>
            <p className="text-sm text-tg-hint">
              Создан {formatRelativeTime(project.created_at)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 mb-4">
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
              project.status
            )} bg-opacity-20`}
          >
            {getStatusLabel(project.status)}
          </span>
          {project.priority && project.priority !== "normal" && (
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-orange-500 bg-opacity-20 text-orange-500">
              {project.priority === "high" ? "Высокий приоритет" : "Критичный"}
            </span>
          )}
        </div>

        {/* Progress */}
        {totalTasks > 0 && (
          <div>
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-tg-hint">Прогресс выполнения</span>
              <span className="font-semibold">{progress}%</span>
            </div>
            <div className="w-full bg-tg-bg rounded-full h-3 mb-2">
              <div
                className="bg-tg-button h-3 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="text-xs text-tg-hint">
              {completedTasks} из {totalTasks} задач завершено
            </div>
          </div>
        )}
      </div>

      {/* Description */}
      {project.description && (
        <div className="p-4">
          <h3 className="text-sm font-semibold mb-2 text-tg-hint">Описание</h3>
          <p className="text-sm bg-tg-secondary-bg rounded-lg p-3">
            {project.description}
          </p>
        </div>
      )}

      {/* Tasks */}
      {tasks && tasks.length > 0 && (
        <div className="p-4">
          <h3 className="text-sm font-semibold mb-3 text-tg-hint">Задачи</h3>

          {/* Task stats */}
          <div className="grid grid-cols-4 gap-2 mb-4">
            <div className="bg-tg-secondary-bg rounded-lg p-2 text-center">
              <Clock className="w-4 h-4 mx-auto mb-1 text-gray-500" />
              <div className="text-xs text-tg-hint">Ожидание</div>
              <div className="text-sm font-semibold">{tasksByStatus.pending.length}</div>
            </div>
            <div className="bg-tg-secondary-bg rounded-lg p-2 text-center">
              <Loader2 className="w-4 h-4 mx-auto mb-1 text-yellow-500" />
              <div className="text-xs text-tg-hint">В работе</div>
              <div className="text-sm font-semibold">{tasksByStatus.in_progress.length}</div>
            </div>
            <div className="bg-tg-secondary-bg rounded-lg p-2 text-center">
              <CheckCircle2 className="w-4 h-4 mx-auto mb-1 text-green-500" />
              <div className="text-xs text-tg-hint">Готово</div>
              <div className="text-sm font-semibold">{tasksByStatus.completed.length}</div>
            </div>
            <div className="bg-tg-secondary-bg rounded-lg p-2 text-center">
              <AlertCircle className="w-4 h-4 mx-auto mb-1 text-red-500" />
              <div className="text-xs text-tg-hint">Ошибки</div>
              <div className="text-sm font-semibold">{tasksByStatus.failed.length}</div>
            </div>
          </div>

          {/* Task list */}
          <div className="space-y-2">
            {tasks.map((task: any) => (
              <div
                key={task.id}
                className="bg-tg-secondary-bg rounded-lg p-3"
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
                    className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
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
        </div>
      )}

      {executeProject.isPending && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-tg-secondary-bg rounded-xl p-6 flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-tg-button" />
            <p className="text-sm">Запускаем AI агентов...</p>
          </div>
        </div>
      )}
    </div>
  );
}
