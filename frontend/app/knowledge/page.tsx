"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "@/components/providers/TelegramProvider";
import KnowledgeSearch from "@/components/KnowledgeSearch";
import KnowledgeStats from "@/components/KnowledgeStats";
import { Search, BarChart3 } from "lucide-react";

export default function KnowledgePage() {
  const router = useRouter();
  const { webApp } = useTelegram();
  const [activeTab, setActiveTab] = useState<"search" | "stats">("search");

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

  return (
    <div className="min-h-screen pb-6 bg-tg-bg">
      {/* Header */}
      <div className="bg-gradient-to-br from-purple-500/10 to-blue-500/10 p-6 border-b border-gray-200 dark:border-gray-800 mb-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-2xl flex items-center justify-center text-2xl shadow-lg">
            📚
          </div>
          <div>
            <h1 className="text-2xl font-bold">База знаний</h1>
            <p className="text-sm text-tg-hint">
              Поиск и аналитика по документам
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 bg-tg-secondary-bg rounded-xl p-1">
          <button
            onClick={() => setActiveTab("search")}
            className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 flex items-center justify-center gap-2 ${
              activeTab === "search"
                ? "bg-tg-button text-tg-button-text shadow-sm"
                : "text-tg-hint"
            }`}
          >
            <Search className="w-4 h-4" />
            Поиск
          </button>
          <button
            onClick={() => setActiveTab("stats")}
            className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 flex items-center justify-center gap-2 ${
              activeTab === "stats"
                ? "bg-tg-button text-tg-button-text shadow-sm"
                : "text-tg-hint"
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Статистика
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="px-4">
        {activeTab === "search" ? <KnowledgeSearch /> : <KnowledgeStats />}
      </div>
    </div>
  );
}
