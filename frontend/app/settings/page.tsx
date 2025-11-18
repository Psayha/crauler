"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "@/components/providers/TelegramProvider";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  Settings as SettingsIcon,
  Bell,
  Moon,
  Sun,
  Globe,
  User,
  Mail,
  Building,
  ChevronRight,
  Loader2,
  CheckCircle2,
} from "lucide-react";

export default function SettingsPage() {
  const router = useRouter();
  const { webApp } = useTelegram();
  const queryClient = useQueryClient();
  const [showSuccess, setShowSuccess] = useState(false);

  // Fetch user settings
  const { data: settings, isLoading } = useQuery({
    queryKey: ["user-settings"],
    queryFn: async () => {
      // Mock settings for now - can be replaced with actual API call
      return {
        theme: "auto",
        notifications: {
          projectUpdates: true,
          taskAssignments: true,
          agentCompletion: true,
          dailyDigest: false,
        },
        language: "ru",
        email: "user@example.com",
        organization: "AI Agency",
      };
    },
  });

  // Update settings mutation
  const updateSettings = useMutation({
    mutationFn: async (newSettings: any) => {
      // Mock mutation - can be replaced with actual API call
      await new Promise((resolve) => setTimeout(resolve, 500));
      return newSettings;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user-settings"] });
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 2000);
    },
  });

  const [localSettings, setLocalSettings] = useState(settings);

  useEffect(() => {
    if (settings) {
      setLocalSettings(settings);
    }
  }, [settings]);

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

  const handleToggle = (key: string, subKey?: string) => {
    if (!localSettings) return;

    const newSettings = { ...localSettings };
    if (subKey) {
      newSettings[key] = {
        ...newSettings[key],
        [subKey]: !newSettings[key][subKey],
      };
    } else {
      newSettings[key] = !newSettings[key];
    }

    setLocalSettings(newSettings);
    updateSettings.mutate(newSettings);
  };

  const handleThemeChange = (theme: string) => {
    if (!localSettings) return;

    const newSettings = { ...localSettings, theme };
    setLocalSettings(newSettings);
    updateSettings.mutate(newSettings);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-tg-link" />
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-6 bg-tg-bg">
      {/* Header */}
      <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 p-6 border-b border-gray-200 dark:border-gray-800 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center text-2xl shadow-lg">
            ⚙️
          </div>
          <div>
            <h1 className="text-2xl font-bold">Настройки</h1>
            <p className="text-sm text-tg-hint">Персонализация приложения</p>
          </div>
        </div>
      </div>

      <div className="px-4 space-y-4">
        {/* Success Message */}
        {showSuccess && (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4 flex items-center gap-3 animate-in slide-in-from-top">
            <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
            <span className="text-sm font-medium text-green-700 dark:text-green-300">
              Настройки сохранены
            </span>
          </div>
        )}

        {/* Profile Section */}
        <div className="bg-tg-secondary-bg rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold flex items-center gap-2">
              <User className="w-4 h-4 text-tg-link" />
              Профиль
            </h3>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            <div className="px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Mail className="w-4 h-4 text-tg-hint" />
                <span className="text-sm">Email</span>
              </div>
              <span className="text-sm text-tg-hint">
                {localSettings?.email}
              </span>
            </div>
            <div className="px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Building className="w-4 h-4 text-tg-hint" />
                <span className="text-sm">Организация</span>
              </div>
              <span className="text-sm text-tg-hint">
                {localSettings?.organization}
              </span>
            </div>
          </div>
        </div>

        {/* Theme Section */}
        <div className="bg-tg-secondary-bg rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold flex items-center gap-2">
              <Moon className="w-4 h-4 text-tg-link" />
              Тема оформления
            </h3>
          </div>
          <div className="p-4 space-y-2">
            <button
              onClick={() => handleThemeChange("light")}
              className={`w-full px-4 py-3 rounded-lg flex items-center justify-between transition-colors ${
                localSettings?.theme === "light"
                  ? "bg-tg-button text-tg-button-text"
                  : "bg-gray-100 dark:bg-gray-800 text-tg-text"
              }`}
            >
              <div className="flex items-center gap-3">
                <Sun className="w-4 h-4" />
                <span className="text-sm font-medium">Светлая</span>
              </div>
              {localSettings?.theme === "light" && (
                <CheckCircle2 className="w-4 h-4" />
              )}
            </button>
            <button
              onClick={() => handleThemeChange("dark")}
              className={`w-full px-4 py-3 rounded-lg flex items-center justify-between transition-colors ${
                localSettings?.theme === "dark"
                  ? "bg-tg-button text-tg-button-text"
                  : "bg-gray-100 dark:bg-gray-800 text-tg-text"
              }`}
            >
              <div className="flex items-center gap-3">
                <Moon className="w-4 h-4" />
                <span className="text-sm font-medium">Тёмная</span>
              </div>
              {localSettings?.theme === "dark" && (
                <CheckCircle2 className="w-4 h-4" />
              )}
            </button>
            <button
              onClick={() => handleThemeChange("auto")}
              className={`w-full px-4 py-3 rounded-lg flex items-center justify-between transition-colors ${
                localSettings?.theme === "auto"
                  ? "bg-tg-button text-tg-button-text"
                  : "bg-gray-100 dark:bg-gray-800 text-tg-text"
              }`}
            >
              <div className="flex items-center gap-3">
                <SettingsIcon className="w-4 h-4" />
                <span className="text-sm font-medium">Системная</span>
              </div>
              {localSettings?.theme === "auto" && (
                <CheckCircle2 className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Notifications Section */}
        <div className="bg-tg-secondary-bg rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold flex items-center gap-2">
              <Bell className="w-4 h-4 text-tg-link" />
              Уведомления
            </h3>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            <div className="px-4 py-3 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Обновления проектов</p>
                <p className="text-xs text-tg-hint">
                  Уведомления о статусе проектов
                </p>
              </div>
              <button
                onClick={() =>
                  handleToggle("notifications", "projectUpdates")
                }
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  localSettings?.notifications?.projectUpdates
                    ? "bg-tg-button"
                    : "bg-gray-300 dark:bg-gray-600"
                }`}
              >
                <div
                  className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    localSettings?.notifications?.projectUpdates
                      ? "translate-x-6"
                      : "translate-x-0.5"
                  }`}
                />
              </button>
            </div>
            <div className="px-4 py-3 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Назначение задач</p>
                <p className="text-xs text-tg-hint">
                  Когда вам назначена новая задача
                </p>
              </div>
              <button
                onClick={() =>
                  handleToggle("notifications", "taskAssignments")
                }
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  localSettings?.notifications?.taskAssignments
                    ? "bg-tg-button"
                    : "bg-gray-300 dark:bg-gray-600"
                }`}
              >
                <div
                  className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    localSettings?.notifications?.taskAssignments
                      ? "translate-x-6"
                      : "translate-x-0.5"
                  }`}
                />
              </button>
            </div>
            <div className="px-4 py-3 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Завершение работы агентов</p>
                <p className="text-xs text-tg-hint">
                  Когда агент завершает задачу
                </p>
              </div>
              <button
                onClick={() =>
                  handleToggle("notifications", "agentCompletion")
                }
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  localSettings?.notifications?.agentCompletion
                    ? "bg-tg-button"
                    : "bg-gray-300 dark:bg-gray-600"
                }`}
              >
                <div
                  className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    localSettings?.notifications?.agentCompletion
                      ? "translate-x-6"
                      : "translate-x-0.5"
                  }`}
                />
              </button>
            </div>
            <div className="px-4 py-3 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Ежедневная сводка</p>
                <p className="text-xs text-tg-hint">
                  Отчёт в конце дня
                </p>
              </div>
              <button
                onClick={() => handleToggle("notifications", "dailyDigest")}
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  localSettings?.notifications?.dailyDigest
                    ? "bg-tg-button"
                    : "bg-gray-300 dark:bg-gray-600"
                }`}
              >
                <div
                  className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    localSettings?.notifications?.dailyDigest
                      ? "translate-x-6"
                      : "translate-x-0.5"
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Language Section */}
        <div className="bg-tg-secondary-bg rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold flex items-center gap-2">
              <Globe className="w-4 h-4 text-tg-link" />
              Язык
            </h3>
          </div>
          <button
            onClick={() => {}}
            className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
          >
            <span className="text-sm">Русский</span>
            <ChevronRight className="w-4 h-4 text-tg-hint" />
          </button>
        </div>

        {/* About Section */}
        <div className="bg-tg-secondary-bg rounded-xl overflow-hidden">
          <div className="px-4 py-3 text-center">
            <p className="text-xs text-tg-hint">AI Agency v1.0.0</p>
            <p className="text-xs text-tg-hint mt-1">
              Powered by OpenAI & Claude
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
