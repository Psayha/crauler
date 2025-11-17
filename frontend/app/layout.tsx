import type { Metadata } from "next";
import "./globals.css";
import { TelegramProvider } from "@/components/providers/TelegramProvider";
import { QueryProvider } from "@/components/providers/QueryProvider";

export const metadata: Metadata = {
  title: "AI Agency",
  description: "Automated digital agency powered by AI agents",
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <head>
        <script src="https://telegram.org/js/telegram-web-app.js" />
      </head>
      <body>
        <TelegramProvider>
          <QueryProvider>
            {children}
          </QueryProvider>
        </TelegramProvider>
      </body>
    </html>
  );
}
