import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  const now = new Date();
  const diff = now.getTime() - d.getTime();

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 7) {
    return formatDate(d);
  } else if (days > 0) {
    return `${days} ${days === 1 ? "день" : "дней"} назад`;
  } else if (hours > 0) {
    return `${hours} ${hours === 1 ? "час" : "часов"} назад`;
  } else if (minutes > 0) {
    return `${minutes} ${minutes === 1 ? "минуту" : "минут"} назад`;
  } else {
    return "только что";
  }
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat("ru-RU").format(num);
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    draft: "bg-gray-500",
    planning: "bg-blue-500",
    in_progress: "bg-yellow-500",
    review: "bg-purple-500",
    completed: "bg-green-500",
    cancelled: "bg-red-500",
    pending: "bg-gray-400",
    failed: "bg-red-600",
  };

  return colors[status] || "bg-gray-400";
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "Черновик",
    planning: "Планирование",
    in_progress: "В работе",
    review: "На проверке",
    completed: "Завершен",
    cancelled: "Отменен",
    pending: "Ожидание",
    failed: "Ошибка",
  };

  return labels[status] || status;
}

// Alias for formatRelativeTime
export const formatDistanceToNow = formatRelativeTime;

export function formatCompact(num: number): string {
  if (num < 1000) return num.toString();
  if (num < 1000000) return `${(num / 1000).toFixed(1)}K`;
  return `${(num / 1000000).toFixed(1)}M`;
}
