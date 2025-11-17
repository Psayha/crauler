"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "@/components/providers/TelegramProvider";
import { api } from "@/lib/api";
import { useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

export default function NewProjectPage() {
  const router = useRouter();
  const { webApp } = useTelegram();
  const [description, setDescription] = useState("");

  const createProject = useMutation({
    mutationFn: (data: { description: string }) => api.createProject(data),
    onSuccess: (data) => {
      if (webApp) {
        webApp.showAlert("Проект успешно создан!", () => {
          router.push(`/projects/${data.id}`);
        });
      } else {
        router.push(`/projects/${data.id}`);
      }
    },
    onError: (error: any) => {
      if (webApp) {
        webApp.showAlert(
          `Ошибка при создании проекта: ${error.message || "Неизвестная ошибка"}`
        );
      }
    },
  });

  useEffect(() => {
    if (webApp) {
      webApp.BackButton.show();
      webApp.BackButton.onClick(() => {
        router.back();
      });

      // Setup MainButton
      const handleCreate = () => {
        if (description.trim()) {
          createProject.mutate({ description: description.trim() });
        } else {
          webApp.showAlert("Пожалуйста, опишите ваш проект");
        }
      };

      webApp.MainButton.text = "Создать проект";
      webApp.MainButton.color = webApp.themeParams.button_color;
      webApp.MainButton.textColor = webApp.themeParams.button_text_color;

      if (description.trim()) {
        webApp.MainButton.show();
      } else {
        webApp.MainButton.hide();
      }

      webApp.MainButton.onClick(handleCreate);

      return () => {
        webApp.BackButton.hide();
        webApp.MainButton.hide();
        webApp.MainButton.offClick(handleCreate);
      };
    }
  }, [webApp, router, description, createProject]);

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="bg-tg-secondary-bg p-4 sticky top-0 z-10">
        <h1 className="text-xl font-bold">Новый проект</h1>
        <p className="text-sm text-tg-hint mt-1">
          Опишите проект, и AI агенты его реализуют
        </p>
      </div>

      {/* Form */}
      <div className="p-4">
        <div className="bg-tg-secondary-bg rounded-xl p-4 mb-4">
          <label htmlFor="description" className="block text-sm font-medium mb-2">
            Описание проекта
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Например: Создать landing page для AI консалтинговой компании с формой контакта и блогом..."
            className="w-full bg-tg-bg text-tg-text rounded-lg p-3 min-h-[200px] resize-none focus:outline-none focus:ring-2 focus:ring-tg-button"
            disabled={createProject.isPending}
          />
          <div className="flex items-center justify-between mt-2 text-xs text-tg-hint">
            <span>Минимум 20 символов</span>
            <span>{description.length} символов</span>
          </div>
        </div>

        {/* Examples */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-tg-hint">Примеры проектов:</h3>

          {[
            {
              icon: "🌐",
              title: "Landing Page",
              desc: "Создать лендинг для SaaS продукта с ценами и формой заявки",
            },
            {
              icon: "📱",
              title: "Mobile App",
              desc: "Разработать приложение для трекинга расходов с диаграммами",
            },
            {
              icon: "📊",
              title: "Marketing Campaign",
              desc: "Создать 3-месячную маркетинговую кампанию для B2B запуска",
            },
          ].map((example, idx) => (
            <button
              key={idx}
              onClick={() => setDescription(example.desc)}
              className="w-full bg-tg-secondary-bg rounded-lg p-3 text-left active:opacity-70 transition-opacity"
              disabled={createProject.isPending}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{example.icon}</span>
                <div className="flex-1">
                  <div className="font-medium text-sm mb-1">{example.title}</div>
                  <div className="text-xs text-tg-hint">{example.desc}</div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {createProject.isPending && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-tg-secondary-bg rounded-xl p-6 flex flex-col items-center gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-tg-button" />
              <p className="text-sm">Создаем проект...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
