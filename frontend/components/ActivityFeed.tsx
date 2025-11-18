"use client";

import { Clock, CheckCircle2, AlertCircle, Zap } from "lucide-react";
import { formatDistanceToNow } from "@/lib/utils";

interface Activity {
  id: string;
  type: "project_created" | "project_completed" | "task_completed" | "task_failed";
  title: string;
  description: string;
  timestamp: string;
  project_id?: string;
}

interface ActivityFeedProps {
  activities?: Activity[];
  isLoading?: boolean;
}

export function ActivityFeed({ activities = [], isLoading }: ActivityFeedProps) {
  const getIcon = (type: Activity["type"]) => {
    switch (type) {
      case "project_created":
        return <Zap className="w-4 h-4 text-blue-500" />;
      case "project_completed":
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case "task_completed":
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case "task_failed":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-3 p-3 bg-tg-secondary-bg rounded-lg animate-pulse">
            <div className="w-8 h-8 bg-gray-300 rounded-full" />
            <div className="flex-1">
              <div className="h-4 bg-gray-300 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-200 rounded w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <div className="text-center py-8">
        <Clock className="w-12 h-12 text-tg-hint mx-auto mb-3 opacity-50" />
        <p className="text-tg-hint text-sm">Пока нет активности</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {activities.map((activity) => (
        <div
          key={activity.id}
          className="flex gap-3 p-3 bg-tg-secondary-bg rounded-lg hover:bg-opacity-80 transition-colors"
        >
          <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-white dark:bg-gray-800 rounded-full">
            {getIcon(activity.type)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-tg-text truncate">
              {activity.title}
            </p>
            <p className="text-xs text-tg-hint truncate">{activity.description}</p>
            <p className="text-xs text-tg-hint mt-1">
              {formatDistanceToNow(activity.timestamp)}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
