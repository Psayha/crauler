"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "@/components/providers/TelegramProvider";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AgentStatusBadge } from "@/components/AgentStatusBadge";
import {
  Loader2,
  ArrowLeft,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  Zap,
  Activity,
} from "lucide-react";
import { formatNumber, formatCompact } from "@/lib/utils";

// Agent types with emojis and descriptions
const AGENT_TYPES = [
  {
    type: "marketing",
    name: "Marketing Agent",
    emoji: "🎯",
    description: "Маркетинговые стратегии и growth",
    color: "from-pink-500 to-rose-500",
  },
  {
    type: "frontend",
    name: "Frontend Developer",
    emoji: "⚛️",
    description: "React/Next.js разработка",
    color: "from-blue-500 to-cyan-500",
  },
  {
    type: "backend",
    name: "Backend Developer",
    emoji: "🔧",
    description: "FastAPI/Node.js архитектура",
    color: "from-green-500 to-emerald-500",
  },
  {
    type: "data_analyst",
    name: "Data Analyst",
    emoji: "📊",
    description: "Анализ данных и визуализация",
    color: "from-purple-500 to-violet-500",
  },
  {
    type: "ux_designer",
    name: "UX/UI Designer",
    emoji: "🎨",
    description: "User research и дизайн",
    color: "from-yellow-500 to-amber-500",
  },
  {
    type: "content_writer",
    name: "Content Writer",
    emoji: "✍️",
    description: "Копирайтинг и контент",
    color: "from-indigo-500 to-blue-500",
  },
  {
    type: "mobile",
    name: "Mobile Developer",
    emoji: "📱",
    description: "iOS/Android разработка",
    color: "from-teal-500 to-green-500",
  },
  {
    type: "devops",
    name: "DevOps Engineer",
    emoji: "⚙️",
    description: "Infrastructure и CI/CD",
    color: "from-orange-500 to-red-500",
  },
  {
    type: "project_manager",
    name: "Project Manager",
    emoji: "📋",
    description: "Agile/Scrum управление",
    color: "from-gray-500 to-slate-500",
  },
  {
    type: "qa_engineer",
    name: "QA Engineer",
    emoji: "🧪",
    description: "Тестирование и качество",
    color: "from-lime-500 to-green-500",
  },
  {
    type: "hr_manager",
    name: "HR Agent",
    emoji: "👥",
    description: "Управление командой агентов",
    color: "from-fuchsia-500 to-pink-500",
  },
];

export default function AgentsPage() {
  const { webApp } = useTelegram();
  const router = useRouter();

  // Fetch agents performance
  const { data: agentsPerformance, isLoading } = useQuery({
    queryKey: ["agents-performance"],
    queryFn: () => api.getAgentsPerformance("30d"),
  });

  // Setup Telegram BackButton
  useEffect(() => {
    if (webApp) {
      webApp.BackButton.show();
      webApp.BackButton.onClick(() => {
        router.back();
      });

      return () => {
        webApp.BackButton.hide();
      };
    }
  }, [webApp, router]);

  const getAgentPerformance = (agentType: string) => {
    if (!agentsPerformance) return null;
    return agentsPerformance.find((a: any) => a.agent_type === agentType);
  };

  const getAgentStatus = (performance: any): "idle" | "working" | "completed" => {
    if (!performance) return "idle";
    if (performance.total_executions === 0) return "idle";
    if (performance.success_rate > 90) return "completed";
    return "working";
  };

  // Calculate overall stats
  const totalExecutions = agentsPerformance?.reduce(
    (sum: number, a: any) => sum + (a.total_executions || 0),
    0
  ) || 0;

  const totalSuccessful = agentsPerformance?.reduce(
    (sum: number, a: any) => sum + (a.successful_executions || 0),
    0
  ) || 0;

  const avgSuccessRate = totalExecutions > 0
    ? ((totalSuccessful / totalExecutions) * 100).toFixed(1)
    : "0";

  const activeAgents = agentsPerformance?.filter((a: any) => a.total_executions > 0).length || 0;

  return (
    <div className="min-h-screen pb-24 bg-tg-bg">
      {/* Header */}
      <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 p-6 sticky top-0 z-10 backdrop-blur-sm border-b border-purple-200 dark:border-purple-800">
        <div className="flex items-center gap-3 mb-4">
          <Activity className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          <h1 className="text-2xl font-bold">Мониторинг агентов</h1>
        </div>

        {/* Overall Stats */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-3">
            <div className="flex items-center gap-1 mb-1">
              <Activity className="w-4 h-4 text-blue-500" />
              <span className="text-xs text-tg-hint">Активных</span>
            </div>
            <p className="text-xl font-bold">{activeAgents}/11</p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-3">
            <div className="flex items-center gap-1 mb-1">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <span className="text-xs text-tg-hint">Успех</span>
            </div>
            <p className="text-xl font-bold">{avgSuccessRate}%</p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-3">
            <div className="flex items-center gap-1 mb-1">
              <Zap className="w-4 h-4 text-yellow-500" />
              <span className="text-xs text-tg-hint">Задач</span>
            </div>
            <p className="text-xl font-bold">{formatCompact(totalExecutions)}</p>
          </div>
        </div>
      </div>

      {/* Agents List */}
      <div className="p-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-tg-hint" />
          </div>
        ) : (
          <div className="space-y-3">
            {AGENT_TYPES.map((agent) => {
              const performance = getAgentPerformance(agent.type);
              const status = getAgentStatus(performance);
              const successRate = performance?.success_rate || 0;
              const totalTasks = performance?.total_executions || 0;
              const avgTime = performance?.avg_execution_time_ms || 0;

              return (
                <div
                  key={agent.type}
                  className="bg-tg-secondary-bg rounded-xl p-4 hover:scale-[1.02] transition-transform active:scale-[0.98]"
                >
                  {/* Agent Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div
                        className={`w-12 h-12 rounded-xl bg-gradient-to-br ${agent.color} flex items-center justify-center text-2xl shadow-lg`}
                      >
                        {agent.emoji}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-sm truncate">
                          {agent.name}
                        </h3>
                        <p className="text-xs text-tg-hint truncate">
                          {agent.description}
                        </p>
                      </div>
                    </div>
                    <AgentStatusBadge status={status} />
                  </div>

                  {/* Agent Stats */}
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-2">
                      <div className="flex items-center gap-1 mb-1">
                        <CheckCircle2 className="w-3 h-3 text-green-500" />
                        <span className="text-xs text-tg-hint">Успех</span>
                      </div>
                      <p className="text-base font-bold">
                        {successRate.toFixed(0)}%
                      </p>
                    </div>

                    <div className="bg-white dark:bg-gray-800 rounded-lg p-2">
                      <div className="flex items-center gap-1 mb-1">
                        <Zap className="w-3 h-3 text-yellow-500" />
                        <span className="text-xs text-tg-hint">Задач</span>
                      </div>
                      <p className="text-base font-bold">{formatCompact(totalTasks)}</p>
                    </div>

                    <div className="bg-white dark:bg-gray-800 rounded-lg p-2">
                      <div className="flex items-center gap-1 mb-1">
                        <Clock className="w-3 h-3 text-blue-500" />
                        <span className="text-xs text-tg-hint">Время</span>
                      </div>
                      <p className="text-base font-bold">
                        {avgTime > 0 ? `${(avgTime / 1000).toFixed(1)}s` : "—"}
                      </p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  {totalTasks > 0 && (
                    <div className="mt-3">
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full bg-gradient-to-r ${agent.color} transition-all duration-500`}
                          style={{ width: `${Math.min(successRate, 100)}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Info Section */}
      <div className="px-4 pb-6">
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
          <div className="flex gap-3">
            <div className="flex-shrink-0 text-2xl">ℹ️</div>
            <div>
              <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                О мониторинге агентов
              </p>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                Здесь отображается производительность всех 11 AI агентов за последние 30 дней.
                Метрики обновляются в реальном времени по мере выполнения задач.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
