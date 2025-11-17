"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { ProjectCard } from "@/components/ProjectCard";
import { Loader2, Plus } from "lucide-react";
import { useTelegram } from "@/components/providers/TelegramProvider";
import { useEffect, useState } from "react";

export default function ProjectsPage() {
  const router = useRouter();
  const { webApp } = useTelegram();
  const [filter, setFilter] = useState<string>("all");

  const { data: projects, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.getProjects(),
  });

  useEffect(() => {
    if (webApp) {
      webApp.BackButton.show();
      webApp.BackButton.onClick(() => {
        router.push("/");
      });

      webApp.MainButton.text = "Создать проект";
      webApp.MainButton.show();
      webApp.MainButton.onClick(() => {
        router.push("/projects/new");
      });

      return () => {
        webApp.BackButton.hide();
        webApp.MainButton.hide();
      };
    }
  }, [webApp, router]);

  const filteredProjects = projects?.filter((project: any) => {
    if (filter === "all") return true;
    return project.status === filter;
  });

  return (
    <div className="min-h-screen pb-24">
      {/* Header */}
      <div className="bg-tg-secondary-bg p-4 sticky top-0 z-10">
        <h1 className="text-xl font-bold mb-4">Все проекты</h1>

        {/* Filter tabs */}
        <div className="flex gap-2 overflow-x-auto">
          {[
            { key: "all", label: "Все" },
            { key: "in_progress", label: "В работе" },
            { key: "completed", label: "Завершены" },
            { key: "draft", label: "Черновики" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                filter === tab.key
                  ? "bg-tg-button text-tg-button-text"
                  : "bg-tg-bg text-tg-hint"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Projects list */}
      <div className="p-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-tg-hint" />
          </div>
        ) : filteredProjects && filteredProjects.length > 0 ? (
          <div className="space-y-3">
            {filteredProjects.map((project: any) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-5xl mb-4">📋</div>
            <p className="text-tg-hint mb-4">
              {filter === "all" ? "У вас пока нет проектов" : "Проектов не найдено"}
            </p>
            <button
              onClick={() => router.push("/projects/new")}
              className="inline-flex items-center gap-2 px-4 py-2 bg-tg-button text-tg-button-text rounded-lg"
            >
              <Plus className="w-4 h-4" />
              Создать проект
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
