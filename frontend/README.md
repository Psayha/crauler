# AI Agency - Telegram Mini App Frontend

Next.js 14 Telegram Mini App для управления AI агентами.

## 🚀 Быстрый старт

### Разработка

1. **Установите зависимости:**
```bash
npm install
# или
yarn install
```

2. **Создайте .env файл:**
```bash
cp .env.example .env.local
```

Настройте переменные:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

3. **Запустите dev сервер:**
```bash
npm run dev
```

Приложение откроется на http://localhost:3000

### Тестирование в Telegram

Для тестирования Mini App в Telegram:

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите токен бота
3. Настройте Mini App:
   - Отправьте `/newapp` в BotFather
   - Укажите URL: `https://your-ngrok-url.com` (или Vercel URL)
   - Загрузите иконку 640x360px

4. Для локальной разработки используйте ngrok:
```bash
ngrok http 3000
```

## 📁 Структура проекта

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout с провайдерами
│   ├── page.tsx                # Dashboard
│   ├── projects/
│   │   ├── page.tsx            # Список проектов
│   │   ├── new/page.tsx        # Создание проекта
│   │   └── [id]/page.tsx       # Детали проекта
│   └── globals.css             # Глобальные стили
├── components/
│   ├── providers/
│   │   ├── TelegramProvider.tsx    # Telegram WebApp SDK
│   │   └── QueryProvider.tsx       # React Query
│   ├── ProjectCard.tsx
│   └── StatsCard.tsx
├── lib/
│   ├── api.ts                  # API клиент
│   ├── websocket.ts            # WebSocket клиент
│   └── utils.ts                # Утилиты
└── package.json
```

## 🎨 Технологии

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**:
  - TanStack Query (React Query) - server state
  - Zustand - client state (опционально)
- **Telegram**: @telegram-apps/sdk
- **HTTP Client**: Axios
- **Real-time**: WebSocket

## 🔧 Основные функции

### Telegram Integration

```typescript
import { useTelegram } from "@/components/providers/TelegramProvider";

const { webApp, user, isReady } = useTelegram();

// Back Button
webApp.BackButton.show();
webApp.BackButton.onClick(() => router.back());

// Main Button
webApp.MainButton.text = "Создать";
webApp.MainButton.show();
webApp.MainButton.onClick(handleCreate);

// Theme
webApp.themeParams.bg_color // Цвет фона
webApp.colorScheme // 'light' | 'dark'

// Haptic Feedback
webApp.HapticFeedback.impactOccurred('medium');
```

### API Calls

```typescript
import { api } from "@/lib/api";

// Authentication
await api.authenticateTelegram(initData);
const user = await api.getCurrentUser();

// Projects
const projects = await api.getProjects();
const project = await api.getProject(id);
await api.createProject({ description });
await api.executeProject(id);

// Tasks
const tasks = await api.getProjectTasks(projectId);
const task = await api.getTask(id);
```

### Real-time Updates

```typescript
import { wsClient } from "@/lib/websocket";

// Connect
wsClient.connect(token);

// Subscribe to project
wsClient.subscribeToProject(projectId);

// Listen for updates
wsClient.on("project_update", (data) => {
  console.log("Project updated:", data);
});

wsClient.on("task_update", (data) => {
  console.log("Task updated:", data);
});

// Unsubscribe
wsClient.unsubscribeFromProject(projectId);
```

## 🚢 Деплой

### Vercel (Recommended)

1. **Push в GitHub:**
```bash
git push origin main
```

2. **Импортируйте в Vercel:**
   - Перейдите на [vercel.com](https://vercel.com)
   - Import repository
   - Настройте Environment Variables:
     ```
     NEXT_PUBLIC_API_URL=https://api.your-domain.com
     NEXT_PUBLIC_WS_URL=wss://api.your-domain.com
     ```

3. **Deploy**
   - Vercel автоматически задеплоит при push
   - Получите production URL

### Netlify

```bash
npm run build
```

Deploy `/.next` folder на Netlify.

### Docker

```dockerfile
FROM node:20-alpine AS base

# Install dependencies
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Build
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production
FROM base AS runner
WORKDIR /app
ENV NODE_ENV production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

## 🎯 Telegram Bot Setup

После деплоя frontend:

1. **Настройте Mini App URL в BotFather:**
```
/mybots
-> Выберите бота
-> Bot Settings
-> Menu Button
-> Configure Menu Button
-> URL: https://your-vercel-app.vercel.app
```

2. **Создайте команду для запуска:**
```
/setcommands

start - Запустить AI Agency
help - Помощь
```

3. **Настройте WebApp:**
```
/newapp
-> Название
-> URL: https://your-vercel-app.vercel.app
-> Загрузите иконку
```

## 🔒 Security

- Все запросы к API защищены JWT токенами
- Telegram initData валидируется на backend
- WebSocket подключения требуют валидный токен
- CORS настроен только для разрешенных доменов

## 📱 Responsive Design

Mini App адаптирован под:
- iPhone (включая безопасные зоны)
- Android
- iPad (landscape/portrait)
- Desktop (для тестирования)

## 🐛 Troubleshooting

### "Telegram WebApp не доступен"
Открывайте через Telegram Mini App, не напрямую в браузере.

### WebSocket не подключается
Проверьте:
- Backend запущен
- NEXT_PUBLIC_WS_URL правильный
- Токен валидный

### Стили Telegram темы не применяются
Telegram передает `themeParams` только внутри Mini App.

## 📚 Документация

- [Next.js 14](https://nextjs.org/docs)
- [Telegram Mini Apps](https://core.telegram.org/bots/webapps)
- [TanStack Query](https://tanstack.com/query/latest)
- [Tailwind CSS](https://tailwindcss.com/docs)

---

**Готово к запуску!** 🚀
