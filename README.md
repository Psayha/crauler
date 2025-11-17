# AI Agency 🤖

Автоматизированное цифровое агентство на базе Claude API, где специализированные AI-агенты работают как единая команда над проектами любой сложности.

## 🎯 Что это?

AI Agency - это система из 10 специализированных AI-агентов, которые работают под управлением Orchestrator (CEO) для выполнения цифровых проектов:

- **Marketing Agent** - CMO, маркетинговые стратегии
- **Frontend Developer** - React/Next.js эксперт
- **Backend Developer** - FastAPI/Node.js архитектор
- **Mobile Developer** - iOS/Android приложения
- **DevOps Engineer** - Infrastructure/CI/CD
- **Data Analyst** - Анализ данных и отчеты
- **UX/UI Designer** - User research и дизайн
- **Project Manager** - Agile/Scrum координация
- **QA Engineer** - Тестирование и QA
- **Content Writer** - SEO и копирайтинг

## 🚀 Быстрый старт

### Требования

- Docker и Docker Compose
- Claude API ключ (от Anthropic)
- Python 3.11+ (для локальной разработки)

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd crauler
```

2. **Создайте .env файл:**
```bash
cp .env.example .env
```

Отредактируйте `.env` и добавьте ваш Claude API ключ:
```env
CLAUDE_API_KEY=your-claude-api-key-here
```

3. **Запустите проект:**
```bash
make build-up
```

Или без Make:
```bash
docker-compose up -d --build
```

4. **Проверьте статус:**
```bash
make ps
```

### Доступ к сервисам

- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

## 📚 Использование

### Создание проекта

**Через API:**
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a landing page for AI consulting company with contact form and blog",
    "organization_id": "test-org-123"
  }'
```

**Через Swagger UI:**
1. Откройте http://localhost:8000/docs
2. Найдите endpoint `POST /api/projects`
3. Нажмите "Try it out"
4. Введите данные и нажмите "Execute"

### Просмотр проектов

```bash
# Получить конкретный проект
curl http://localhost:8000/api/projects/{project_id}

# Список всех проектов
curl http://localhost:8000/api/projects
```

### Запуск выполнения проекта

```bash
curl -X POST http://localhost:8000/api/projects/{project_id}/execute
```

## 🛠️ Команды Make

```bash
make help           # Показать все команды
make build          # Собрать Docker образы
make up             # Запустить сервисы
make down           # Остановить сервисы
make logs           # Показать логи всех сервисов
make logs-backend   # Логи backend
make shell          # Открыть shell в backend контейнере
make shell-db       # Открыть PostgreSQL shell
make test           # Запустить тесты
make restart        # Перезапустить все сервисы
make clean          # Удалить контейнеры и volumes
```

## 📁 Структура проекта

```
ai-agency/
├── backend/
│   ├── app/
│   │   ├── agents/           # AI агенты
│   │   │   └── orchestrator.py
│   │   ├── models/           # SQLAlchemy модели
│   │   │   ├── project.py
│   │   │   ├── task.py
│   │   │   └── agent_execution.py
│   │   ├── services/         # Сервисы
│   │   │   └── claude_service.py
│   │   ├── api/              # API endpoints
│   │   │   ├── projects.py
│   │   │   └── tasks.py
│   │   ├── database/         # Database
│   │   │   └── connection.py
│   │   ├── config.py         # Настройки
│   │   └── main.py           # FastAPI app
│   └── requirements.txt
├── docker/
│   └── Dockerfile.backend
├── docker-compose.yml
├── Makefile
└── README.md
```

## 🔧 Разработка

### Локальный запуск (без Docker)

1. **Установите зависимости:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Запустите PostgreSQL и Redis:**
```bash
docker-compose up -d postgres redis
```

3. **Запустите backend:**
```bash
cd backend
uvicorn app.main:app --reload
```

### Подключение к базе данных

```bash
# Через Docker
make shell-db

# Или напрямую
psql postgresql://aiagency:securepassword@localhost:5432/ai_agency
```

### Просмотр логов

```bash
# Все логи
make logs

# Только backend
make logs-backend

# Только PostgreSQL
make logs-postgres
```

## 🧪 Тестирование

```bash
# Запустить все тесты
make test

# Или внутри контейнера
make shell
pytest
```

## 📖 API Документация

### Основные endpoints:

#### Projects

- `POST /api/projects` - Создать проект
- `GET /api/projects` - Список проектов
- `GET /api/projects/{project_id}` - Детали проекта
- `POST /api/projects/{project_id}/execute` - Запустить выполнение

#### Tasks

- `GET /api/tasks/{task_id}` - Детали задачи
- `GET /api/tasks/project/{project_id}` - Задачи проекта

#### Health

- `GET /` - Информация о сервисе
- `GET /health` - Health check

Полная документация доступна на http://localhost:8000/docs

## 🎨 Примеры использования

### Пример 1: Landing Page

```json
{
  "description": "Create a modern landing page for AI SaaS product with pricing, features, and contact form",
  "organization_id": "my-org"
}
```

### Пример 2: Mobile App

```json
{
  "description": "Build a React Native expense tracker app with categories, charts, and cloud sync",
  "organization_id": "my-org"
}
```

### Пример 3: Marketing Campaign

```json
{
  "description": "Develop a 3-month marketing campaign for B2B SaaS launch including content strategy and SEO",
  "organization_id": "my-org"
}
```

## 🐛 Troubleshooting

### Backend не запускается

```bash
# Проверьте логи
make logs-backend

# Проверьте что PostgreSQL запущен
make logs-postgres

# Перезапустите сервисы
make restart
```

### Database connection errors

```bash
# Убедитесь что PostgreSQL готов
docker-compose exec postgres pg_isready

# Пересоздайте БД
make clean
make build-up
```

### Claude API errors

- Проверьте что `CLAUDE_API_KEY` установлен в `.env`
- Проверьте баланс вашего аккаунта Anthropic
- Проверьте логи: `make logs-backend`

## 📄 Лицензия

MIT License

## 👥 Авторы

Разработано на базе Claude API (Anthropic)

## 🔗 Ссылки

- [Claude API Documentation](https://docs.anthropic.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)

---

**Готово к запуску!** 🚀

Если у вас есть вопросы или проблемы, создайте issue в репозитории.
