"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "@/components/providers/TelegramProvider";
import {
  Settings as SettingsIcon,
  Bell,
  Moon,
  Sun,
  Globe,
  User,
  Loader2,
  CheckCircle2,
  ChevronRight,
} from "lucide-react";

interface UserSettings {
  notifications: {
    projectUpdates: boolean;
    taskAssignments: boolean;
    agentCompletion: boolean;
    dailyDigest: boolean;
  };
  language: string;
}

const DEFAULT_SETTINGS: UserSettings = {
  notifications: {
    projectUpdates: true,
    taskAssignments: true,
    agentCompletion: true,
    dailyDigest: false,
  },
  language: "ru",
};

export default function SettingsPage() {
  const router = useRouter();
  const { webApp, user } = useTelegram();
  const [showSuccess, setShowSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);

  // Load settings from Telegram CloudStorage
  useEffect(() => {
    const loadSettings = async () => {
      if (!webApp?.CloudStorage) {
        setIsLoading(false);
        return;
      }

      try {
        webApp.CloudStorage.getItems(
          ["notifications", "language"],
          (error: any, result: any) => {
            if (error) {
              console.error("Error loading settings:", error);
              setIsLoading(false);
              return;
            }

            const loadedSettings: UserSettings = {
              notifications: result.notifications
                ? JSON.parse(result.notifications)
                : DEFAULT_SETTINGS.notifications,
              language: result.language || DEFAULT_SETTINGS.language,
            };

            setSettings(loadedSettings);
            setIsLoading(false);
          }
        );
      } catch (error) {
        console.error("Error accessing CloudStorage:", error);
        setIsLoading(false);
      }
    };

    loadSettings();
  }, [webApp]);

  // Save settings to Telegram CloudStorage
  const saveSettings = (newSettings: UserSettings) => {
    if (!webApp?.CloudStorage) return;

    webApp.CloudStorage.setItem(
      "notifications",
      JSON.stringify(newSettings.notifications),
      (error: any) => {
        if (error) {
          console.error("Error saving notifications:", error);
          return;
        }
      }
    );

    webApp.CloudStorage.setItem(
      "language",
      newSettings.language,
      (error: any) => {
        if (error) {
          console.error("Error saving language:", error);
          return;
        }
      }
    );

    setSettings(newSettings);
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 2000);
  };

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

  const handleToggle = (subKey: string) => {
    const newSettings = {
      ...settings,
      notifications: {
        ...settings.notifications,
        [subKey]: !settings.notifications[subKey as keyof typeof settings.notifications],
      },
    };
    saveSettings(newSettings);
  };

  const handleThemeChange = (theme: string) => {
    // Theme is controlled by Telegram directly
    // We can trigger haptic feedback
    if (webApp?.HapticFeedback) {
      webApp.HapticFeedback.impactOccurred("light");
    }
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
                <User className="w-4 h-4 text-tg-hint" />
                <span className="text-sm">Имя</span>
              </div>
              <span className="text-sm text-tg-hint">
                {user?.first_name || user?.username || "User"}
              </span>
            </div>
            {user?.username && (
              <div className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-tg-hint">@</span>
                  <span className="text-sm">Username</span>
                </div>
                <span className="text-sm text-tg-hint">@{user.username}</span>
              </div>
            )}
          </div>
        </div>

        {/* Theme Info */}
        <div className="bg-tg-secondary-bg rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold flex items-center gap-2">
              <Moon className="w-4 h-4 text-tg-link" />
              Тема оформления
            </h3>
          </div>
          <div className="px-4 py-3">
            <p className="text-sm text-tg-hint">
              Тема приложения автоматически синхронизируется с темой Telegram.
              Измените тему в настройках Telegram для изменения темы приложения.
            </p>
            <div className="mt-3 flex items-center gap-2">
              <div className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                <div className="flex items-center gap-2">
                  {webApp?.colorScheme === "dark" ? (
                    <Moon className="w-4 h-4" />
                  ) : (
                    <Sun className="w-4 h-4" />
                  )}
                  <span className="text-sm">
                    {webApp?.colorScheme === "dark" ? "Тёмная" : "Светлая"}
                  </span>
                </div>
              </div>
            </div>
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
                onClick={() => handleToggle("projectUpdates")}
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  settings.notifications.projectUpdates
                    ? "bg-tg-button"
                    : "bg-gray-300 dark:bg-gray-600"
                }`}
              >
                <div
                  className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    settings.notifications.projectUpdates
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
                onClick={() => handleToggle("taskAssignments")}
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  settings.notifications.taskAssignments
                    ? "bg-tg-button"
                    : "bg-gray-300 dark:bg-gray-600"
                }`}
              >
                <div
                  className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    settings.notifications.taskAssignments
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
                onClick={() => handleToggle("agentCompletion")}
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  settings.notifications.agentCompletion
                    ? "bg-tg-button"
                    : "bg-gray-300 dark:bg-gray-600"
                }`}
              >
                <div
                  className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    settings.notifications.agentCompletion
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
                onClick={() => handleToggle("dailyDigest")}
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  settings.notifications.dailyDigest
                    ? "bg-tg-button"
                    : "bg-gray-300 dark:bg-gray-600"
                }`}
              >
                <div
                  className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    settings.notifications.dailyDigest
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
