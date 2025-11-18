"use client";

import { Plus, Search, BarChart3, Users } from "lucide-react";
import { useRouter } from "next/navigation";

export function QuickActions() {
  const router = useRouter();

  const actions = [
    {
      icon: <Plus className="w-5 h-5" />,
      label: "Новый проект",
      description: "Создать проект",
      onClick: () => router.push("/projects/new"),
      color: "bg-blue-500",
    },
    {
      icon: <Search className="w-5 h-5" />,
      label: "Поиск",
      description: "Knowledge Base",
      onClick: () => router.push("/knowledge"),
      color: "bg-purple-500",
    },
    {
      icon: <BarChart3 className="w-5 h-5" />,
      label: "Аналитика",
      description: "Статистика",
      onClick: () => router.push("/analytics"),
      color: "bg-green-500",
    },
    {
      icon: <Users className="w-5 h-5" />,
      label: "Агенты",
      description: "Мониторинг",
      onClick: () => router.push("/agents"),
      color: "bg-orange-500",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3">
      {actions.map((action, index) => (
        <button
          key={index}
          onClick={action.onClick}
          className="flex items-center gap-3 p-4 bg-tg-secondary-bg rounded-xl hover:scale-105 transition-transform active:scale-95"
        >
          <div
            className={`w-10 h-10 flex items-center justify-center rounded-full text-white ${action.color}`}
          >
            {action.icon}
          </div>
          <div className="text-left flex-1 min-w-0">
            <p className="font-medium text-sm text-tg-text truncate">
              {action.label}
            </p>
            <p className="text-xs text-tg-hint truncate">{action.description}</p>
          </div>
        </button>
      ))}
    </div>
  );
}
