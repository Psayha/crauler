"use client";

import { Activity, CheckCircle2, Clock } from "lucide-react";

interface AgentStatusBadgeProps {
  status: "idle" | "working" | "completed";
  label?: string;
}

export function AgentStatusBadge({ status, label }: AgentStatusBadgeProps) {
  const getConfig = () => {
    switch (status) {
      case "working":
        return {
          icon: <Activity className="w-3 h-3 animate-pulse" />,
          color: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
          text: label || "Работает",
        };
      case "completed":
        return {
          icon: <CheckCircle2 className="w-3 h-3" />,
          color: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
          text: label || "Готов",
        };
      case "idle":
      default:
        return {
          icon: <Clock className="w-3 h-3" />,
          color: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
          text: label || "Ожидает",
        };
    }
  };

  const config = getConfig();

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}
    >
      {config.icon}
      {config.text}
    </span>
  );
}
