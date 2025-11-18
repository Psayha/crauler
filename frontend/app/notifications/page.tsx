"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "@/components/providers/TelegramProvider";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import {
  Bell,
  CheckCircle2,
  AlertCircle,
  Info,
  Zap,
  Clock,
  Loader2,
  ExternalLink,
} from "lucide-react";

type NotificationType = "all" | "project" | "task" | "agent" | "system";

interface Notification {
  id: string;
  user_id: string;
  project_id?: string;
  type: string;
  title: string;
  message?: string;
  is_read: boolean;
  action_url?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export default function NotificationsPage() {
  const router = useRouter();
  const { webApp } = useTelegram();
  const [filterType, setFilterType] = useState<NotificationType>("all");

  // Fetch notifications from API
  const { data: notificationsData, isLoading } = useQuery({
    queryKey: ["notifications", filterType],
    queryFn: () => api.getNotifications(
      filterType !== "all" ? { filter_type: filterType } : undefined
    ),
  });

  const notifications = notificationsData?.notifications || [];
  const unreadCount = notificationsData?.unread_count || 0;

  // Setup Telegram buttons
  useEffect(() => {
    if (webApp) {
      webApp.BackButton.show();
      webApp.BackButton.onClick(() => {
        router.push("/");
      });

      return () => {
        webApp.BackButton.hide();
      };
    }
  }, [webApp, router]);

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case "project_completed":
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case "task_failed":
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case "agent_completed":
        return <Zap className="w-5 h-5 text-blue-500" />;
      case "system":
        return <Info className="w-5 h-5 text-purple-500" />;
      default:
        return <Bell className="w-5 h-5 text-gray-500" />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case "project_completed":
        return "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800";
      case "task_failed":
        return "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800";
      case "agent_completed":
        return "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800";
      case "system":
        return "bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800";
      default:
        return "bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700";
    }
  };

  const filteredNotifications = notifications;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-tg-link" />
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-24 bg-tg-bg">
      {/* Header */}
      <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 p-6 border-b border-gray-200 dark:border-gray-800 mb-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center text-2xl shadow-lg relative">
            🔔
            {unreadCount > 0 && (
              <div className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-xs font-bold text-white">
                {unreadCount}
              </div>
            )}
          </div>
          <div>
            <h1 className="text-2xl font-bold">Уведомления</h1>
            <p className="text-sm text-tg-hint">
              {unreadCount > 0
                ? `${unreadCount} непрочитанных`
                : "Все прочитаны"}
            </p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
          {[
            { type: "all" as NotificationType, label: "Все", icon: Bell },
            {
              type: "project" as NotificationType,
              label: "Проекты",
              icon: CheckCircle2,
            },
            { type: "task" as NotificationType, label: "Задачи", icon: Clock },
            { type: "agent" as NotificationType, label: "Агенты", icon: Zap },
            { type: "system" as NotificationType, label: "Система", icon: Info },
          ].map(({ type, label, icon: Icon }) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap flex items-center gap-2 ${
                filterType === type
                  ? "bg-tg-button text-tg-button-text"
                  : "bg-tg-secondary-bg text-tg-hint"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Notifications List */}
      <div className="px-4 space-y-3">
        {filteredNotifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-20 h-20 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
              <Bell className="w-10 h-10 text-gray-400" />
            </div>
            <p className="text-tg-hint text-sm">Нет уведомлений</p>
          </div>
        ) : (
          filteredNotifications.map((notification) => (
            <div
              key={notification.id}
              className={`rounded-xl border p-4 ${getNotificationColor(
                notification.type
              )} ${
                notification.is_read ? "opacity-60" : ""
              } transition-opacity`}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  {getNotificationIcon(notification.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-sm mb-1">
                    {notification.title}
                    {!notification.is_read && (
                      <span className="ml-2 inline-block w-2 h-2 bg-blue-500 rounded-full" />
                    )}
                  </h3>
                  {notification.message && (
                    <p className="text-sm text-tg-text mb-2">
                      {notification.message}
                    </p>
                  )}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 text-xs text-tg-hint">
                      <Clock className="w-3 h-3" />
                      {formatRelativeTime(notification.created_at)}
                    </div>
                    {notification.action_url && (
                      <button
                        onClick={() =>
                          router.push(notification.action_url!)
                        }
                        className="text-xs text-tg-link hover:underline flex items-center gap-1"
                      >
                        Открыть
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
