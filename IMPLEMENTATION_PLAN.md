# AI Agency - План реализации (Telegram Mini App)
## Обновлено: 2025-11-17

## 🎯 Архитектура решения

```
┌─────────────────────────────────────────────┐
│         TELEGRAM MINI APP (Next.js)         │
│     ┌──────────────────────────────┐        │
│     │   Dashboard / Projects       │        │
│     │   Task Visualization         │        │
│     │   Agent Monitoring           │        │
│     │   Real-time Updates (WS)     │        │
│     └──────────────┬───────────────┘        │
└────────────────────┼────────────────────────┘
                     │ HTTPS/WSS
┌────────────────────▼────────────────────────┐
│         BACKEND API (FastAPI)               │
│  ┌──────────────────────────────────────┐  │
│  │  Telegram Auth Middleware            │  │
│  │  REST API + WebSocket                │  │
│  │  Orchestrator + 10 AI Agents         │  │
│  │  Task Execution Engine               │  │
│  └──────────────────────────────────────┘  │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│       PostgreSQL + Redis + Celery           │
└─────────────────────────────────────────────┘
```

## ✅ Реализовано (Phase 1)

- ✅ Backend API (FastAPI)
- ✅ PostgreSQL модели (Projects, Tasks, AgentExecution)
- ✅ 10 специализированных AI агентов
- ✅ Orchestrator для декомпозиции проектов
- ✅ AgentExecutor с управлением зависимостями
- ✅ REST API с Swagger docs
- ✅ Docker Compose setup

## 🔄 Phase 2: Telegram Mini App Integration

### 2.1 Backend Updates

#### Telegram Authentication
```python
# backend/app/auth/telegram.py
- Валидация Telegram WebApp initData
- JWT токены для API access
- Middleware для защиты endpoints
- User model с telegram_id
```

#### WebSocket для Real-time
```python
# backend/app/websockets/
- WebSocket manager
- Project execution updates
- Task status changes
- Agent activity notifications
```

#### API Extensions
```python
# Новые endpoints:
GET  /api/users/me              - Текущий пользователь
POST /api/auth/telegram         - Telegram OAuth
GET  /api/projects/my           - Мои проекты
WS   /ws/projects/{id}          - Real-time updates
```

### 2.2 Frontend: Telegram Mini App (Next.js)

#### Структура проекта
```
frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Dashboard
│   ├── projects/
│   │   ├── page.tsx            # Projects list
│   │   ├── new/page.tsx        # Create project
│   │   └── [id]/
│   │       ├── page.tsx        # Project details
│   │       └── tasks/[taskId]/page.tsx
│   └── agents/
│       └── page.tsx            # Agents overview
├── components/
│   ├── ui/                     # shadcn/ui components
│   ├── project/
│   │   ├── ProjectCard.tsx
│   │   ├── CreateProjectForm.tsx
│   │   ├── TaskTree.tsx
│   │   └── AgentActivity.tsx
│   ├── telegram/
│   │   ├── TelegramProvider.tsx
│   │   ├── BackButton.tsx
│   │   └── MainButton.tsx
│   └── layout/
│       ├── Header.tsx
│       └── Navigation.tsx
├── lib/
│   ├── api.ts                  # API client
│   ├── telegram.ts             # Telegram WebApp SDK
│   ├── websocket.ts            # WebSocket client
│   └── utils.ts
├── hooks/
│   ├── useTelegram.ts
│   ├── useWebSocket.ts
│   ├── useProjects.ts
│   └── useAgents.ts
└── styles/
    └── globals.css             # Tailwind + custom
```

#### Key Features

**1. Telegram Integration**
```typescript
// hooks/useTelegram.ts
- Telegram WebApp SDK инициализация
- Theme detection (light/dark)
- BackButton, MainButton управление
- Haptic feedback
- Viewport расширение
```

**2. Dashboard**
```typescript
// app/page.tsx
- Список активных проектов
- Статистика (всего проектов, задач, токенов)
- Быстрые действия
- Последняя активность агентов
```

**3. Create Project**
```typescript
// app/projects/new/page.tsx
- Multi-step форма
- Project type selection
- AI-powered description
- Priority & deadline
- Real-time token estimation
```

**4. Project Details**
```typescript
// app/projects/[id]/page.tsx
- Project overview
- Task dependency tree visualization
- Agent assignments
- Progress tracking
- Execution controls (Start/Pause/Cancel)
- Real-time WebSocket updates
```

**5. Task Visualization**
```typescript
// components/project/TaskTree.tsx
- Дерево задач с зависимостями
- Статус каждой задачи (pending/in_progress/completed/failed)
- Assigned agent с индикатором
- Estimated vs actual tokens
- Timeline/Gantt view
```

**6. Agent Monitoring**
```typescript
// app/agents/page.tsx
- Список всех 10 агентов
- Current status (idle/working)
- Performance metrics
- Task history
- Temperature settings
```

### 2.3 Tech Stack Updates

#### Frontend Dependencies
```json
{
  "dependencies": {
    "next": "14.2.0",
    "@telegram-apps/sdk": "^1.0.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.5.0",
    "axios": "^1.6.0",
    "socket.io-client": "^4.7.0",
    "react-hook-form": "^7.50.0",
    "zod": "^3.22.0",
    "@radix-ui/react-*": "latest",
    "tailwindcss": "^3.4.0",
    "lucide-react": "^0.300.0",
    "recharts": "^2.10.0",
    "react-flow-renderer": "^10.0.0"
  }
}
```

#### Backend Dependencies
```txt
# Добавить в requirements.txt
python-telegram-bot==20.7
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
fastapi-websocket==0.1.0
python-socketio==5.11.0
celery[redis]==5.3.4
```

### 2.4 Database Schema Updates

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10) DEFAULT 'ru',
    is_premium BOOLEAN DEFAULT FALSE,
    credits_balance INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP DEFAULT NOW()
);

-- Update projects table
ALTER TABLE projects ADD COLUMN user_id UUID REFERENCES users(id);
ALTER TABLE projects ADD COLUMN telegram_thread_id BIGINT;

-- Notifications table
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    type VARCHAR(50), -- project_completed, task_failed, etc
    title VARCHAR(255),
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User settings
CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    theme VARCHAR(20) DEFAULT 'auto',
    language VARCHAR(10) DEFAULT 'ru',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    auto_execute BOOLEAN DEFAULT FALSE,
    settings JSONB DEFAULT '{}'::jsonb
);
```

## 🔄 Phase 3: Celery & Background Jobs

### 3.1 Celery Setup

```python
# backend/app/celery_app.py
from celery import Celery

celery_app = Celery(
    "ai_agency",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

# Tasks
@celery_app.task
def execute_project_async(project_id: str):
    """Асинхронное выполнение проекта"""
    pass

@celery_app.task
def execute_task_async(task_id: str):
    """Асинхронное выполнение задачи"""
    pass

@celery_app.task
def send_telegram_notification(user_id: str, message: str):
    """Отправка уведомлений"""
    pass
```

### 3.2 Docker Compose Update

```yaml
# docker-compose.yml
services:
  # ... existing services

  celery-worker:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  celery-beat:
    build: ./backend
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
```

## 📱 Phase 4: Telegram Bot Companion (Optional)

Минимальный бот для:
- Запуска Mini App
- Push уведомлений
- Быстрые команды

```python
# bot/main.py
from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler

async def start(update: Update, context):
    keyboard = [[
        InlineKeyboardButton(
            "🚀 Открыть AI Agency",
            web_app=WebAppInfo(url="https://your-domain.com")
        )
    ]]
    await update.message.reply_text(
        "Добро пожаловать в AI Agency!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
```

## 🎨 UI/UX Концепция

### Цветовая схема
```css
/* Адаптация под Telegram Theme */
:root {
  --tg-theme-bg-color: var(--telegram-bg-color);
  --tg-theme-text-color: var(--telegram-text-color);
  --tg-theme-hint-color: var(--telegram-hint-color);
  --tg-theme-link-color: var(--telegram-link-color);
  --tg-theme-button-color: var(--telegram-button-color);
  --tg-theme-button-text-color: var(--telegram-button-text-color);
}
```

### Ключевые экраны

**Dashboard**
```
┌────────────────────────────────┐
│  👋 Привет, @username          │
│  💰 Credits: 850               │
├────────────────────────────────┤
│  📊 Статистика                 │
│  • 5 активных проектов         │
│  • 23 задачи выполнено         │
│  • 125K токенов использовано   │
├────────────────────────────────┤
│  🚀 Создать проект       [+]   │
├────────────────────────────────┤
│  📱 Landing Page App           │
│  ⚡ In Progress • 65%          │
│  👥 5 агентов                  │
├────────────────────────────────┤
│  🎯 Marketing Campaign         │
│  ✅ Completed                  │
│  👥 3 агента                   │
└────────────────────────────────┘
```

**Project Details**
```
┌────────────────────────────────┐
│  ← Landing Page App            │
├────────────────────────────────┤
│  Status: In Progress (65%)     │
│  ━━━━━━━━━━░░░░░░              │
├────────────────────────────────┤
│  📋 Задачи (12/20)             │
│  ├─ ✅ UX Research             │
│  ├─ ⚡ Frontend Dev (60%)      │
│  ├─ 🔄 Backend API             │
│  └─ ⏳ Content Writing         │
├────────────────────────────────┤
│  👥 Активные агенты            │
│  • Frontend Dev 🟢             │
│  • Backend Dev 🟢              │
│  • UX Designer 🟡              │
├────────────────────────────────┤
│  [Пауза] [Отменить] [Детали]  │
└────────────────────────────────┘
```

## 🔧 Development Roadmap

### Week 1-2: Backend Auth & WebSocket
- [ ] Telegram authentication middleware
- [ ] JWT tokens
- [ ] User model & CRUD
- [ ] WebSocket setup
- [ ] Real-time updates logic

### Week 3-4: Frontend Mini App Core
- [ ] Next.js project setup
- [ ] Telegram SDK integration
- [ ] Theme adaptation
- [ ] API client с TanStack Query
- [ ] WebSocket client

### Week 5-6: UI Components
- [ ] Dashboard page
- [ ] Projects list & cards
- [ ] Create project form
- [ ] Project details page
- [ ] Task tree visualization
- [ ] Agent monitoring

### Week 7: Celery Integration
- [ ] Celery setup
- [ ] Background task execution
- [ ] Progress tracking
- [ ] Error handling

### Week 8: Polish & Testing
- [ ] UI/UX improvements
- [ ] Error handling
- [ ] Loading states
- [ ] Unit tests
- [ ] Integration tests

## 🚀 Deployment

### Frontend Hosting
```bash
# Vercel (recommended for Mini App)
vercel deploy --prod

# Environment variables
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com
TELEGRAM_BOT_TOKEN=your_bot_token
```

### Backend Hosting
```bash
# Railway / Render / DigitalOcean
docker-compose -f docker-compose.prod.yml up -d

# Environment variables
CLAUDE_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
TELEGRAM_BOT_TOKEN=...
JWT_SECRET=...
FRONTEND_URL=https://your-mini-app.vercel.app
```

## 📊 Success Metrics

- ✅ Mini App загружается < 2s
- ✅ WebSocket latency < 200ms
- ✅ Project creation < 30s
- ✅ Real-time updates работают
- ✅ Responsive на всех экранах
- ✅ Telegram Theme правильно применяется
- ✅ Haptic feedback работает

---

**Next Step:** Начинаем с Telegram authentication в backend и базовой структуры Mini App! 🚀
