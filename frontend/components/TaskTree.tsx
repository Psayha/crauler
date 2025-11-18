"use client";

import { CheckCircle2, Clock, AlertCircle, Loader2, Users, ArrowRight } from "lucide-react";
import { getStatusColor, getStatusLabel } from "@/lib/utils";

interface Task {
  id: string;
  title: string;
  description?: string;
  status: string;
  assigned_agent?: string;
  dependencies?: string[];
  priority?: string;
}

interface TaskTreeProps {
  tasks: Task[];
}

export function TaskTree({ tasks }: TaskTreeProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case "in_progress":
        return <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />;
      case "failed":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getAgentEmoji = (agentType?: string) => {
    const emojis: Record<string, string> = {
      marketing: "🎯",
      frontend: "⚛️",
      backend: "🔧",
      data_analyst: "📊",
      ux_designer: "🎨",
      content_writer: "✍️",
      mobile: "📱",
      devops: "⚙️",
      project_manager: "📋",
      qa_engineer: "🧪",
      hr_manager: "👥",
    };
    return agentType ? emojis[agentType] || "🤖" : "🤖";
  };

  // Build dependency graph
  const taskMap = new Map(tasks.map((t) => [t.id, t]));
  const dependencyGraph = new Map<string, string[]>();

  tasks.forEach((task) => {
    if (task.dependencies && task.dependencies.length > 0) {
      dependencyGraph.set(task.id, task.dependencies);
    }
  });

  // Group tasks by level (topological sort visualization)
  const getTaskLevel = (taskId: string, visited = new Set<string>()): number => {
    if (visited.has(taskId)) return 0;
    visited.add(taskId);

    const deps = dependencyGraph.get(taskId) || [];
    if (deps.length === 0) return 0;

    const depLevels = deps.map((depId) => getTaskLevel(depId, visited));
    return Math.max(...depLevels) + 1;
  };

  const tasksWithLevels = tasks.map((task) => ({
    ...task,
    level: getTaskLevel(task.id),
  }));

  // Sort by level, then by status priority
  const sortedTasks = tasksWithLevels.sort((a, b) => {
    if (a.level !== b.level) return a.level - b.level;

    const statusPriority: Record<string, number> = {
      in_progress: 0,
      pending: 1,
      completed: 2,
      failed: 3,
    };

    return (statusPriority[a.status] || 4) - (statusPriority[b.status] || 4);
  });

  // Group by level
  const levelGroups = new Map<number, typeof sortedTasks>();
  sortedTasks.forEach((task) => {
    const group = levelGroups.get(task.level) || [];
    group.push(task);
    levelGroups.set(task.level, group);
  });

  return (
    <div className="space-y-6">
      {Array.from(levelGroups.entries())
        .sort(([a], [b]) => a - b)
        .map(([level, levelTasks], groupIndex) => (
          <div key={level} className="relative">
            {/* Level indicator */}
            <div className="flex items-center gap-2 mb-3">
              <div className="text-xs font-semibold text-tg-hint uppercase tracking-wider">
                {level === 0 ? "Начальные задачи" : `Уровень ${level}`}
              </div>
              <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700" />
            </div>

            {/* Tasks in this level */}
            <div className="space-y-3">
              {levelTasks.map((task, taskIndex) => (
                <div key={task.id} className="relative">
                  {/* Dependency arrows */}
                  {task.dependencies && task.dependencies.length > 0 && taskIndex === 0 && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 text-gray-400">
                      <ArrowRight className="w-4 h-4 rotate-90" />
                    </div>
                  )}

                  <div className="bg-tg-secondary-bg rounded-xl p-4 hover:shadow-md transition-shadow">
                    {/* Task header */}
                    <div className="flex items-start gap-3 mb-2">
                      {getStatusIcon(task.status)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-sm truncate flex-1">
                            {task.title}
                          </h4>
                          {task.priority && task.priority !== "normal" && (
                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400">
                              {task.priority === "high" ? "Высокий" : "Критич."}
                            </span>
                          )}
                        </div>

                        {task.description && (
                          <p className="text-xs text-tg-hint line-clamp-2 mb-2">
                            {task.description}
                          </p>
                        )}

                        {/* Agent assignment */}
                        {task.assigned_agent && (
                          <div className="flex items-center gap-2">
                            <div className="flex items-center gap-1 px-2 py-1 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                              <span className="text-sm">
                                {getAgentEmoji(task.assigned_agent)}
                              </span>
                              <span className="text-xs font-medium text-purple-700 dark:text-purple-300">
                                {task.assigned_agent}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Status badge */}
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(
                          task.status
                        )} bg-opacity-20 flex-shrink-0`}
                      >
                        {getStatusLabel(task.status)}
                      </span>
                    </div>

                    {/* Dependencies info */}
                    {task.dependencies && task.dependencies.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                        <div className="flex items-center gap-1 text-xs text-tg-hint">
                          <ArrowRight className="w-3 h-3" />
                          <span>
                            Зависит от {task.dependencies.length}{" "}
                            {task.dependencies.length === 1
                              ? "задачи"
                              : task.dependencies.length < 5
                              ? "задач"
                              : "задач"}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
    </div>
  );
}
