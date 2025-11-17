# Промпт для Claude Code: Реализация SaaS "Здоровье проекта"

## КОНТЕКСТ И ЦЕЛЬ

Ты опытный full-stack разработчик. Твоя задача - создать полнофункциональный SaaS-сервис для комплексного аудита веб-сайтов. Сервис должен анализировать технические аспекты, SEO, качество контента и готовность к использованию в LLM/RAG системах.

Прилагается детальное техническое задание (FINAL_REQUIREMENTS.md) с полным описанием функциональности.

## ПОШАГОВЫЙ ПЛАН РЕАЛИЗАЦИИ

### ШАГ 1: Инициализация проекта

1. Создай структуру директорий:
```
project-health-checker/
├── backend/
├── frontend/
├── docker/
├── docs/
├── scripts/
└── tests/
```

2. Инициализируй git репозиторий с .gitignore

3. Создай README.md с описанием проекта

### ШАГ 2: Backend - Базовая структура

1. В `backend/` создай структуру FastAPI приложения:
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── settings.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── project.py
│   │   ├── audit.py
│   │   ├── page.py
│   │   └── issue.py
│   ├── schemas/
│   │   └── [аналогичная структура]
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── projects.py
│   │       ├── audits.py
│   │       └── router.py
│   ├── services/
│   ├── crawling/
│   ├── parsing/
│   ├── rules/
│   └── workers/
├── alembic/
├── requirements.txt
├── .env.example
└── Makefile
```

2. Создай requirements.txt со всеми зависимостями:
```
fastapi==0.109.0
uvicorn[standard]==0.25.0
sqlalchemy==2.0.23
alembic==1.13.0
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.4
httpx==0.25.2
beautifulsoup4==4.12.2
lxml==4.9.4
playwright==1.40.0
pydantic==2.5.2
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pytest==7.4.3
pytest-asyncio==0.21.1
```

3. Реализуй базовую конфигурацию и подключение к БД

### ШАГ 3: Модели данных

1. Реализуй SQLAlchemy модели согласно схеме БД из ТЗ
2. Особое внимание удели:
   - Связям между таблицами
   - Индексам для производительности
   - JSON полям для гибких настроек
   - Шифрованию sensitive данных

### ШАГ 4: Аутентификация и авторизация

1. Реализуй JWT-based аутентификацию
2. Добавь OAuth2 с Яндекс ID
3. Реализуй систему ролей (Owner, Admin, Analyst, Viewer)
4. Добавь rate limiting
5. Реализуй 2FA через TOTP

### ШАГ 5: Краулер

1. В `app/crawling/` создай:
   - `crawler.py` - основной класс краулера
   - `fetcher.py` - async HTTP client
   - `robots.py` - парсер robots.txt
   - `url_manager.py` - управление очередью URL
   - `rate_limiter.py` - контроль RPS

2. Реализуй:
   - Соблюдение robots.txt
   - Rate limiting (1-2 RPS с jitter)
   - Retry логику с exponential backoff
   - Обработку redirects
   - Поддержку sitemap.xml
   - Игнорирование non-HTML ресурсов

### ШАГ 6: JS-рендеринг

1. В `app/crawling/js_renderer.py`:
   - Интеграция с Playwright
   - Pool браузеров для производительности
   - Ожидание networkidle
   - Блокировка ненужных ресурсов
   - Снимки DOM и скриншоты
   - Обработка infinite scroll

### ШАГ 7: Парсеры

1. В `app/parsing/` создай:
   - `html_parser.py` - извлечение мета, заголовков, ссылок
   - `content_parser.py` - извлечение и очистка текста
   - `structured_data.py` - парсинг JSON-LD, microdata
   - `resource_parser.py` - анализ CSS, JS, изображений

2. Реализуй:
   - Извлечение всех SEO-релевантных тегов
   - Построение карты внутренних ссылок
   - Анализ иерархии заголовков
   - Извлечение чистого текста для анализа

### ШАГ 8: Rule Engine

1. В `app/rules/` создай:
   - `base.py` - базовый класс правила
   - `technical/` - технические проверки
   - `seo/` - SEO проверки
   - `content/` - контентные проверки
   - `llm/` - LLM-readiness проверки
   - `engine.py` - движок выполнения правил

2. Реализуй систему правил с:
   - Версионированием
   - Настраиваемыми порогами
   - Приоритетами (critical, major, minor, info)
   - Возможностью отключения per проект

### ШАГ 9: LLM-модуль

1. В `app/services/llm/` создай:
   - `chunker.py` - разбиение на чанки
   - `entity_extractor.py` - NER
   - `fact_checker.py` - проверка консистентности
   - `answerability.py` - оценка Q&A потенциала
   - `embeddings.py` - генерация векторов

2. Интегрируй с GigaChat API для:
   - Генерации вопросов по контенту
   - Оценки качества ответов
   - Проверки противоречий

### ШАГ 10: Celery Workers

1. В `app/workers/` создай:
   - `celery_app.py` - конфигурация Celery
   - `tasks/audit.py` - задачи аудита
   - `tasks/crawl.py` - задачи краулинга
   - `tasks/export.py` - задачи экспорта

2. Настрой:
   - Redis как broker и backend
   - Celery Beat для scheduled задач
   - Приоритеты очередей
   - Retry политики
   - Monitoring через Flower

### ШАГ 11: API Endpoints

1. Реализуй все endpoints из спецификации в ТЗ
2. Добавь:
   - Pydantic схемы для валидации
   - Dependency injection для auth
   - Pagination для списков
   - Фильтры и сортировки
   - OpenAPI документацию

### ШАГ 12: Интеграции

1. В `app/integrations/` создай:
   - `yandex_metrika.py` - OAuth и API клиент
   - `yandex_webmaster.py` - OAuth и API клиент
   - `yandex_speller.py` - проверка орфографии

2. Реализуй:
   - OAuth flow для Яндекс
   - Периодическую синхронизацию данных
   - Обработку rate limits
   - Кеширование результатов

### ШАГ 13: Экспорт и отчеты

1. В `app/services/export/` создай:
   - `json_export.py`
   - `csv_export.py`
   - `pdf_export.py` (используй ReportLab)
   - `markdown_export.py`
   - `rag_dataset.py`

2. Реализуй:
   - Шаблоны отчетов
   - Брендирование
   - Асинхронную генерацию
   - Загрузку в S3

### ШАГ 14: Frontend - React приложение

1. В `frontend/` создай React + TypeScript проект:
```
frontend/
├── src/
│   ├── api/
│   ├── components/
│   │   ├── common/
│   │   ├── layout/
│   │   ├── charts/
│   │   └── tables/
│   ├── features/
│   │   ├── auth/
│   │   ├── projects/
│   │   ├── audits/
│   │   └── reports/
│   ├── hooks/
│   ├── store/
│   ├── types/
│   └── utils/
├── package.json
└── vite.config.ts
```

2. Установи зависимости:
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "@reduxjs/toolkit": "^2.0.1",
    "antd": "^5.12.0",
    "recharts": "^2.10.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.0.0"
  }
}
```

3. Реализуй страницы:
   - Dashboard с метриками
   - Список проектов
   - Детали проекта с историей
   - Процесс аудита (real-time)
   - Результаты с фильтрами
   - Сравнение аудитов
   - Настройки и интеграции

### ШАГ 15: Docker и DevOps

1. Создай Dockerfile для backend:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. Создай docker-compose.yml:
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: site_health
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    depends_on:
      - db
      - redis
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db/site_health
      REDIS_URL: redis://redis:6379
    ports:
      - "8000:8000"

  worker:
    build: ./backend
    command: celery -A app.workers.celery_app worker -l info
    depends_on:
      - db
      - redis
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db/site_health
      REDIS_URL: redis://redis:6379

  beat:
    build: ./backend
    command: celery -A app.workers.celery_app beat -l info
    depends_on:
      - db
      - redis

  flower:
    build: ./backend
    command: celery -A app.workers.celery_app flower
    ports:
      - "5555:5555"
    depends_on:
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  postgres_data:
  redis_data:
```

3. Создай Makefile для удобства:
```makefile
.PHONY: help build up down logs shell test

help:
	@echo "Available commands:"
	@echo "  make build  - Build containers"
	@echo "  make up     - Start services"
	@echo "  make down   - Stop services"
	@echo "  make logs   - Show logs"
	@echo "  make shell  - Enter backend shell"
	@echo "  make test   - Run tests"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec backend bash

test:
	docker-compose exec backend pytest

migrate:
	docker-compose exec backend alembic upgrade head

seed:
	docker-compose exec backend python scripts/seed_data.py
```

### ШАГ 16: Тестирование

1. В `backend/tests/` создай:
   - `test_auth.py` - тесты аутентификации
   - `test_crawler.py` - тесты краулера
   - `test_rules.py` - тесты правил
   - `test_api.py` - тесты API endpoints
   - `conftest.py` - fixtures

2. Настрой pytest с coverage:
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=app --cov-report=html --cov-report=term
```

### ШАГ 17: Мониторинг и логирование

1. Добавь структурированное логирование:
```python
# app/core/logging.py
import structlog

def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

2. Добавь метрики Prometheus:
```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

audit_counter = Counter('audits_total', 'Total audits', ['status'])
crawl_duration = Histogram('crawl_duration_seconds', 'Crawl duration')
active_audits = Gauge('active_audits', 'Currently running audits')
```

### ШАГ 18: Безопасность

1. Реализуй:
   - CORS настройки
   - Rate limiting через slowapi
   - SQL injection защиту (SQLAlchemy ORM)
   - XSS защиту (Pydantic validation)
   - CSRF токены
   - Шифрование sensitive данных

### ШАГ 19: Производительность

1. Добавь:
   - Redis кеширование
   - Database connection pooling
   - Async везде где можно
   - Batch processing для bulk операций
   - Lazy loading для больших данных

### ШАГ 20: Документация и финализация

1. Создай документацию:
   - API документация (автоматически через FastAPI)
   - README с инструкциями запуска
   - CONTRIBUTING.md
   - Архитектурные диаграммы

2. Добавь примеры:
   - `.env.example`
   - Postman коллекцию
   - Тестовые данные для seed

## ВАЖНЫЕ ПРИНЦИПЫ РЕАЛИЗАЦИИ

1. **Модульность**: Каждый компонент должен быть независимым и тестируемым
2. **Async First**: Используй асинхронность везде где возможно
3. **Type Safety**: Строгая типизация через Pydantic и TypeScript
4. **Error Handling**: Обработка всех возможных ошибок с понятными сообщениями
5. **Logging**: Структурированное логирование всех важных операций
6. **Testing**: Покрытие тестами > 80%
7. **Security**: Безопасность by default
8. **Performance**: Оптимизация с первого дня
9. **Documentation**: Документируй код и API

## ПОСЛЕДОВАТЕЛЬНОСТЬ ДЕЙСТВИЙ

1. Начни с backend структуры и моделей
2. Реализуй аутентификацию
3. Создай простой краулер
4. Добавь базовые правила проверки
5. Реализуй API endpoints
6. Добавь Celery для async задач
7. Создай минимальный UI
8. Добавь JS-рендеринг
9. Реализуй LLM модуль
10. Добавь интеграции
11. Реализуй экспорт
12. Допиши полноценный UI
13. Покрой тестами
14. Настрой Docker
15. Добавь мониторинг

## РЕЗУЛЬТАТ

Полнофункциональный SaaS для аудита сайтов с:
- Масштабируемой архитектурой
- Современным стеком технологий
- Полным покрытием функциональности из ТЗ
- Production-ready кодом
- Документацией и тестами

Начни реализацию с шага 1 и последовательно выполняй все шаги, создавая полноценный работающий код. Не используй заглушки или псевдокод - пиши реальную, работающую реализацию. Если возникнут вопросы по конкретным деталям реализации, уточни их перед написанием кода.

## ДОПОЛНИТЕЛЬНЫЕ УКАЗАНИЯ

1. **Используй современные практики Python**:
   - Type hints везде
   - Dataclasses/Pydantic для DTO
   - Context managers для ресурсов
   - Pathlib для работы с путями

2. **Оптимизируй запросы к БД**:
   - Используй eager loading для связей
   - Batch inserts/updates
   - Правильные индексы
   - Query optimization

3. **Обеспечь масштабируемость**:
   - Stateless backend
   - Horizontal scaling ready
   - Cache стратегия
   - Queue для тяжелых операций

4. **Следуй стандартам**:
   - PEP 8 для Python
   - ESLint + Prettier для JS/TS
   - Conventional commits
   - Semantic versioning

5. **Production readiness**:
   - Health checks
   - Graceful shutdown
   - Circuit breakers
   - Retry policies
   - Dead letter queues

Удачи в реализации! Создай качественный, production-ready код, который можно будет сразу деплоить и использовать.
