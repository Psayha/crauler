"use client";

import { usePathname, useRouter } from "next/navigation";
import { Home, FolderKanban, Search, Bell, Settings } from "lucide-react";

export function BottomNav() {
  const pathname = usePathname();
  const router = useRouter();

  const navItems = [
    {
      icon: Home,
      label: "Главная",
      path: "/",
    },
    {
      icon: FolderKanban,
      label: "Проекты",
      path: "/projects",
    },
    {
      icon: Search,
      label: "Поиск",
      path: "/knowledge",
    },
    {
      icon: Bell,
      label: "Активность",
      path: "/notifications",
    },
    {
      icon: Settings,
      label: "Настройки",
      path: "/settings",
    },
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-tg-secondary-bg border-t border-gray-200 dark:border-gray-800 safe-area-bottom">
      <div className="grid grid-cols-5 h-16">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.path ||
                          (item.path !== "/" && pathname?.startsWith(item.path));

          return (
            <button
              key={item.path}
              onClick={() => router.push(item.path)}
              className={`flex flex-col items-center justify-center gap-1 transition-colors ${
                isActive
                  ? "text-tg-button"
                  : "text-tg-hint"
              }`}
            >
              <Icon
                className={`w-5 h-5 ${
                  isActive ? "fill-current" : ""
                }`}
              />
              <span className="text-xs font-medium">{item.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
