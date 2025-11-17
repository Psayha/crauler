"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

interface ITelegramContext {
  webApp: any;
  user: any;
  isReady: boolean;
}

const TelegramContext = createContext<ITelegramContext>({
  webApp: null,
  user: null,
  isReady: false,
});

export const useTelegram = () => useContext(TelegramContext);

export function TelegramProvider({ children }: { children: ReactNode }) {
  const [webApp, setWebApp] = useState<any>(null);
  const [user, setUser] = useState<any>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp;

      if (tg) {
        // Initialize Telegram WebApp
        tg.ready();
        tg.expand();

        // Enable closing confirmation
        tg.enableClosingConfirmation();

        // Apply theme
        const themeParams = tg.themeParams;
        if (themeParams) {
          document.documentElement.style.setProperty(
            "--tg-theme-bg-color",
            themeParams.bg_color || "#ffffff"
          );
          document.documentElement.style.setProperty(
            "--tg-theme-text-color",
            themeParams.text_color || "#000000"
          );
          document.documentElement.style.setProperty(
            "--tg-theme-hint-color",
            themeParams.hint_color || "#999999"
          );
          document.documentElement.style.setProperty(
            "--tg-theme-link-color",
            themeParams.link_color || "#2481cc"
          );
          document.documentElement.style.setProperty(
            "--tg-theme-button-color",
            themeParams.button_color || "#2481cc"
          );
          document.documentElement.style.setProperty(
            "--tg-theme-button-text-color",
            themeParams.button_text_color || "#ffffff"
          );
          document.documentElement.style.setProperty(
            "--tg-theme-secondary-bg-color",
            themeParams.secondary_bg_color || "#f4f4f5"
          );

          // Apply dark theme if needed
          if (tg.colorScheme === "dark") {
            document.documentElement.setAttribute("data-theme", "dark");
          }
        }

        setWebApp(tg);
        setUser(tg.initDataUnsafe?.user);
        setIsReady(true);
      } else {
        // Development mode without Telegram
        console.warn("Telegram WebApp не доступен. Режим разработки.");
        setIsReady(true);
      }
    }
  }, []);

  return (
    <TelegramContext.Provider value={{ webApp, user, isReady }}>
      {children}
    </TelegramContext.Provider>
  );
}
