# Техническое задание: SaaS сервис "Здоровье проекта"
## Версия 3.0 - Полная реализация

## 1. ОБЩЕЕ ОПИСАНИЕ

### 1.1 Назначение системы
SaaS-платформа для комплексного аудита веб-сайтов с фокусом на:
- Технический аудит (производительность, ошибки, безопасность)
- SEO-аудит (мета-теги, структура, внутренняя перелинковка)
- Контентный анализ (качество, уникальность, читабельность)
- LLM-readiness (готовность к нейропоиску и RAG-системам)
- Мониторинг изменений и трендов
- Интеграции с Яндекс.Метрика и Яндекс.Вебмастер

### 1.2 Целевая аудитория
- SEO-специалисты
- Владельцы сайтов
- Digital-агентства
- Разработчики
- Контент-менеджеры

### 1.3 Ключевые особенности
- Multi-tenancy архитектура
- Версионирование правил проверки
- JS-рендеринг для SPA
- Baseline и исторические сравнения
- Экспорт в множество форматов
- API для интеграций

## 2. ФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ

### 2.1 Управление пользователями и организациями

#### 2.1.1 Регистрация и аутентификация
- Email/пароль регистрация с подтверждением
- OAuth2 (Яндекс ID, VK ID)
- 2FA через TOTP
- Восстановление пароля
- Сессии с refresh tokens

#### 2.1.2 Организации и роли
- Создание организаций
- Приглашение пользователей
- Роли: Owner, Admin, Analyst, Viewer
- Квоты на проекты и проверки
- Биллинг per организация

#### 2.1.3 Тарифные планы
- Free: 1 проект, 100 страниц/проверка, 1 проверка/день
- Startup: 5 проектов, 500 страниц, 10 проверок/день
- Business: 20 проектов, 2000 страниц, без лимита проверок
- Enterprise: кастомные лимиты

### 2.2 Управление проектами

#### 2.2.1 CRUD проектов
- Создание с указанием домена
- Настройки per проект:
  - Активные правила и их пороги
  - Лимиты краулинга
  - JS-рендеринг вкл/выкл
  - Исключения URL (regex)
  - HTTP Basic Auth если нужно
  - Custom headers
  - Sitemap URL
  - Яндекс.Метрика counter ID
  - Яндекс.Вебмастер host ID

#### 2.2.2 Команды проекта
- Назначение пользователей на проект
- Права доступа per проект
- История изменений настроек

### 2.3 Краулинг и сбор данных

#### 2.3.1 Краулер
- **Соблюдение robots.txt** (с возможностью override для владельцев)
- **Rate limiting**: 1-2 RPS с jitter
- **Глубина**: настраиваемая (default: 5)
- **Лимиты**: max_pages (default: 500), max_time (default: 30 min)
- **User-Agent**: идентифицируемый бот
- **Обработка redirects**: до 5 редиректов
- **Retry logic**: 3 попытки с exponential backoff
- **Обработка ошибок**: таймауты, 4xx, 5xx
- **Поддержка**: gzip, deflate, br
- **Игнорирование**: файлы (pdf, zip, exe), mailto:, tel:

#### 2.3.2 JS-рендеринг (Playwright)
- **Браузер**: Chromium headless
- **Режимы**:
  - Выборочный (критичные страницы)
  - Полный (все страницы)
- **Ожидание**: networkidle, custom selectors
- **Таймаут**: 30 сек на страницу
- **Ресурсы**: блокировка ненужных (шрифты, трекеры)
- **Снимки**: DOM после рендера, скриншоты
- **Обработка**: infinite scroll, lazy loading

#### 2.3.3 Сбор ресурсов
- CSS файлы (размер, количество)
- JS файлы (размер, количество, покрытие)
- Изображения (размер, формат, alt-тексты)
- Шрифты (количество, размер)
- Внешние ресурсы (CDN, third-party)

### 2.4 Парсинг и анализ

#### 2.4.1 HTML парсинг
- **Мета-теги**: title, description, keywords, og:*, twitter:*
- **Заголовки**: H1-H6 структура и иерархия
- **Ссылки**: внутренние, внешние, broken, nofollow
- **Изображения**: src, alt, title, размеры
- **Формы**: action, method, inputs
- **Structured data**: JSON-LD, Microdata, RDFa
- **Canonical**, hreflang, pagination tags

#### 2.4.2 Контент парсинг
- **Извлечение текста**: clean text без HTML
- **Разбивка на блоки**: параграфы, списки, таблицы
- **Статистика**: количество слов, символов
- **Языковой анализ**: определение языка
- **Читабельность**: Flesch score адаптированный для русского

#### 2.4.3 Технический анализ
- **Производительность**: TTFB, DOM ready, full load
- **Размеры**: HTML, общий вес страницы
- **HTTP**: статус коды, заголовки, сжатие
- **Безопасность**: HTTPS, CSP, X-Frame-Options
- **Mobile**: viewport, responsive images

### 2.5 Правила проверки (Rule Engine)

#### 2.5.1 Категории правил

**Technical (технические)**
- Битые ссылки (404, 5xx)
- Медленная загрузка (TTFB > 1.5s)
- Отсутствие HTTPS
- Отсутствие сжатия
- Большие изображения (> 200kb)
- Отсутствие кеширования
- Mixed content
- Console errors (из JS-рендера)
- Недоступные ресурсы

**SEO Meta (SEO метаданные)**
- Отсутствие title/description
- Дубли title/description
- Слишком короткие/длинные title (< 30 или > 60)
- Слишком короткие/длинные description (< 70 или > 160)
- Отсутствие H1 или множественные H1
- Нарушение иерархии заголовков
- Отсутствие alt у изображений
- Отсутствие canonical
- Проблемы с hreflang

**Content Quality (качество контента)**
- Слишком мало текста (< 300 слов)
- Орфографические ошибки (через Яндекс.Спеллер API)
- Низкая читабельность
- Переспам ключевыми словами
- Duplicate content (> 70% совпадения)
- Тошнота текста
- Водность текста

**LLM Readiness (готовность к LLM)**
- Плохая структурированность для чанкинга
- Отсутствие четких ответов на вопросы
- Конфликтующие факты на разных страницах
- Недостаточное покрытие сущностей
- Отсутствие FAQ/Q&A разметки
- Слабая внутренняя перелинковка контекста
- Отсутствие сводной информации (summary)

**Structured Data (структурированные данные)**
- Отсутствие Schema.org разметки
- Невалидная JSON-LD разметка
- Неполная разметка (missing required fields)
- Несоответствие разметки контенту
- Отсутствие breadcrumbs
- Отсутствие Organization/LocalBusiness

**UX/Navigation (UX и навигация)**
- Broken внутренние ссылки
- Orphan pages (страницы без входящих ссылок)
- Слишком глубокая вложенность (> 4 клика от главной)
- Отсутствие хлебных крошек
- Медленный Critical Rendering Path
- Отсутствие мобильной версии
- Попапы и interstitials

**Cross-page Consistency (консистентность)**
- Разные форматы дат
- Разные названия одной сущности
- Конфликтующие цены/характеристики
- Несогласованная навигация
- Различия в footer/header

#### 2.5.2 Версионирование правил
- Каждое правило имеет версию
- История изменений правил
- Возможность rollback
- A/B тестирование правил
- Changelog для пользователей

#### 2.5.3 Кастомизация правил
- Включение/отключение per проект
- Настройка порогов (thresholds)
- Настройка severity (critical, major, minor, info)
- Игнорирование для конкретных URL
- Создание custom правил (для Enterprise)

### 2.6 Scoring и приоритизация

#### 2.6.1 Health Score
- Общий score: 0-100
- Категориальные scores
- Взвешенная формула:
  - Critical: -20 points
  - Major: -10 points  
  - Minor: -5 points
  - Info: -1 point
- Нормализация на количество страниц

#### 2.6.2 Приоритизация
- Impact analysis (сколько страниц затронуто)
- Effort estimation (сложность исправления)
- Business priority (на основе трафика)
- Quick wins (легко исправить, большой impact)

### 2.7 LLM-Readiness модуль

#### 2.7.1 Chunkability анализ
- Оценка структуры для разбиения на чанки
- Определение оптимального размера чанка
- Выявление логических границ контента
- Связность между чанками
- Метрики:
  - Средний размер параграфа
  - Наличие подзаголовков
  - Соотношение текст/разметка

#### 2.7.2 Answerability Score
- Анализ вопросно-ответной структуры
- Покрытие типовых вопросов (что, где, когда, как, почему)
- Полнота информации для ответов
- Использование LLM API для проверки:
  - Генерация вопросов по контенту
  - Попытка ответить на вопросы
  - Оценка качества ответов

#### 2.7.3 Entity Coverage
- Извлечение именованных сущностей (NER)
- Граф связей между сущностями
- Полнота описания сущностей
- Консистентность упоминаний

#### 2.7.4 Fact Consistency
- Извлечение фактов (даты, числа, утверждения)
- Поиск противоречий между страницами
- Версионность фактов (устаревшие данные)
- Fact checking через внешние источники

#### 2.7.5 RAG Dataset Generation
- Автоматическая генерация чанков
- Создание embeddings (через API)
- Метаданные для каждого чанка
- Экспорт в форматах:
  - JSONL для OpenAI
  - Parquet для векторных БД
  - CSV для простой обработки

### 2.8 Мониторинг и тренды

#### 2.8.1 Baseline
- Первый аудит = baseline
- Ручная установка baseline
- Сравнение с baseline:
  - Новые проблемы
  - Решенные проблемы
  - Регрессии

#### 2.8.2 Scheduled аудиты
- Ежедневные, еженедельные, ежемесячные
- Уведомления о критичных изменениях
- Автоматические отчеты

#### 2.8.3 Trend анализ
- График Health Score
- Топ растущих проблем
- Velocity исправлений
- Прогнозирование

#### 2.8.4 Alerts
- Email уведомления
- Webhook интеграции
- Telegram бот
- Настраиваемые условия

### 2.9 Интеграции

#### 2.9.1 Яндекс.Метрика
- OAuth авторизация
- Получение данных:
  - Трафик по страницам
  - Показатель отказов
  - Время на странице
  - Конверсии
- Приоритизация проблем по трафику

#### 2.9.2 Яндекс.Вебмастер
- OAuth авторизация
- Получение данных:
  - Индексация
  - Поисковые запросы
  - Позиции
  - Ошибки краулинга
- Сопоставление с найденными проблемами

#### 2.9.3 Внешние API
- Яндекс.Спеллер (проверка орфографии)
- GigaChat API (LLM проверки)
- PageSpeed Insights API
- Whois API (данные о домене)

### 2.10 Экспорт и отчеты

#### 2.10.1 Форматы экспорта
- **JSON**: полный дамп данных
- **CSV/XLSX**: таблицы с проблемами
- **PDF**: брендированные отчеты
- **Markdown**: технические отчеты
- **HTML**: интерактивные отчеты

#### 2.10.2 Типы отчетов
- **Executive Summary**: для руководства
- **Technical Report**: для разработчиков
- **SEO Report**: для SEO-специалистов
- **Content Report**: для контент-менеджеров
- **LLM Readiness**: для AI-инженеров

#### 2.10.3 Кастомизация отчетов
- Выбор секций
- Брендирование (лого, цвета)
- Шаблоны отчетов
- Автоматическая отправка

### 2.11 API

#### 2.11.1 REST API
- OpenAPI 3.0 спецификация
- Версионирование (/api/v1/)
- Rate limiting per API key
- Endpoints:
  - Projects CRUD
  - Audits (create, list, get)
  - Pages (list, get details)
  - Issues (list, filter, export)
  - Rules (list, configure)
  - Webhooks (CRUD)

#### 2.11.2 Webhooks
- События: audit_completed, issues_found, score_changed
- Retry логика
- Подпись для верификации
- История доставок

#### 2.11.3 GraphQL (опционально)
- Для сложных запросов
- Оптимизация загрузки данных
- Real-time subscriptions

## 3. НЕФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ

### 3.1 Производительность
- Краулинг: до 100 страниц/минуту
- Анализ: до 1000 правил/секунду
- API: < 200ms для простых запросов
- UI: < 3s полная загрузка страницы
- Конкурентность: 100+ одновременных аудитов

### 3.2 Масштабируемость
- Горизонтальное масштабирование workers
- Кеширование результатов
- CDN для статики
- База данных с репликацией
- Очередь задач с приоритетами

### 3.3 Надежность
- Uptime: 99.9%
- Автоматический restart failed jobs
- Circuit breaker для внешних API
- Graceful degradation
- Backup стратегия

### 3.4 Безопасность
- HTTPS everywhere
- OAuth2 + JWT
- Rate limiting
- SQL injection защита
- XSS защита
- CSRF токены
- Логирование security events
- Шифрование sensitive данных

### 3.5 Мониторинг
- Метрики: Prometheus
- Логи: структурированные JSON
- Трейсинг: OpenTelemetry
- Дашборды: Grafana
- Алерты: критичные события

## 4. ТЕХНИЧЕСКАЯ АРХИТЕКТУРА

### 4.1 Backend Stack
- **Язык**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Миграции**: Alembic
- **Валидация**: Pydantic v2
- **Тесты**: pytest + coverage

### 4.2 Асинхронная обработка
- **Queue**: Celery 5.3+
- **Broker**: Redis
- **Backend**: Redis
- **Scheduler**: Celery Beat
- **Monitoring**: Flower

### 4.3 Краулинг и рендеринг
- **HTTP**: httpx (async)
- **HTML**: BeautifulSoup4 + lxml
- **JS render**: Playwright
- **URL**: urllib3
- **Robots**: robotparser

### 4.4 База данных
- **Primary**: PostgreSQL 15+
- **Cache**: Redis
- **Search**: PostgreSQL FTS (позже ElasticSearch)
- **Vectors**: pgvector для embeddings

### 4.5 Frontend Stack
- **Framework**: React 18 + TypeScript
- **State**: Redux Toolkit + RTK Query
- **UI**: Ant Design или MUI
- **Charts**: Recharts
- **Build**: Vite
- **Tests**: Jest + React Testing Library

### 4.6 DevOps
- **Containers**: Docker + Docker Compose
- **Orchestration**: Kubernetes (production)
- **CI/CD**: GitLab CI / GitHub Actions
- **Registry**: GitLab Registry
- **Secrets**: HashiCorp Vault / K8s secrets

### 4.7 Инфраструктура
- **Cloud**: Yandex.Cloud / VK Cloud
- **CDN**: Yandex CDN / CloudFlare
- **Storage**: S3-compatible для отчетов
- **DNS**: Managed DNS
- **SSL**: Let's Encrypt

## 5. СТРУКТУРА БАЗЫ ДАННЫХ

### 5.1 Основные таблицы

```sql
-- Пользователи и организации
users (id, email, password_hash, name, created_at, verified, mfa_secret)
organizations (id, name, slug, plan, created_at, owner_id)
organization_members (id, org_id, user_id, role, joined_at)

-- Проекты
projects (id, org_id, name, domain, settings_json, created_at, created_by)
project_members (id, project_id, user_id, permissions_json)

-- Аудиты
audits (id, project_id, status, type, started_at, completed_at, error)
audit_jobs (id, audit_id, celery_task_id, status, progress, logs)

-- Страницы
pages (id, audit_id, url, status_code, title, description, content_hash)
page_resources (id, page_id, type, url, size, load_time)
page_metrics (id, page_id, ttfb, dom_ready, full_load, word_count)
rendered_pages (id, page_id, html_snapshot, screenshot_url, js_errors)

-- Контент
content_blocks (id, page_id, type, content, position, heading_level)
entities (id, page_id, type, name, mentions_count, context)
facts (id, page_id, fact_text, confidence, source)

-- Проблемы
issues (id, audit_id, page_id, rule_id, severity, details_json)
issue_history (id, project_id, issue_hash, first_seen, last_seen, fixed_at)

-- Правила
rules (id, code, name, category, current_version)
rule_versions (id, rule_id, version, condition_json, severity, message)
project_rules (id, project_id, rule_id, enabled, custom_threshold)

-- Интеграции
integrations (id, project_id, type, credentials_encrypted, settings)
integration_data (id, integration_id, metric, value, fetched_at)

-- Тренды
baselines (id, project_id, audit_id, set_at, set_by)
health_scores (id, audit_id, total_score, category_scores_json)
trend_points (id, project_id, metric, value, recorded_at)

-- Экспорт
exports (id, audit_id, format, url, created_at, expires_at)
scheduled_exports (id, project_id, format, schedule_cron, recipients)
```

### 5.2 Индексы
- pages(audit_id, url)
- issues(audit_id, severity)
- issues(page_id, rule_id)
- health_scores(project_id, created_at)
- pages(url, status_code) для поиска 404

### 5.3 Партиционирование
- issues по audit_id
- page_metrics по дате
- trend_points по месяцам

## 6. API СПЕЦИФИКАЦИЯ

### 6.1 Аутентификация
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/verify-email
POST /api/v1/auth/reset-password
```

### 6.2 Организации
```
GET    /api/v1/organizations
POST   /api/v1/organizations
GET    /api/v1/organizations/{org_id}
PUT    /api/v1/organizations/{org_id}
DELETE /api/v1/organizations/{org_id}
POST   /api/v1/organizations/{org_id}/invite
```

### 6.3 Проекты
```
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/{project_id}
PUT    /api/v1/projects/{project_id}
DELETE /api/v1/projects/{project_id}
PUT    /api/v1/projects/{project_id}/settings
```

### 6.4 Аудиты
```
POST   /api/v1/projects/{project_id}/audits
GET    /api/v1/projects/{project_id}/audits
GET    /api/v1/audits/{audit_id}
DELETE /api/v1/audits/{audit_id}
GET    /api/v1/audits/{audit_id}/status
POST   /api/v1/audits/{audit_id}/cancel
```

### 6.5 Результаты
```
GET    /api/v1/audits/{audit_id}/pages
GET    /api/v1/audits/{audit_id}/issues
GET    /api/v1/audits/{audit_id}/score
GET    /api/v1/audits/{audit_id}/compare?with={audit_id}
```

### 6.6 Экспорт
```
POST   /api/v1/audits/{audit_id}/export
GET    /api/v1/exports/{export_id}/download
```

### 6.7 Правила
```
GET    /api/v1/rules
GET    /api/v1/projects/{project_id}/rules
PUT    /api/v1/projects/{project_id}/rules/{rule_id}
```

### 6.8 Интеграции
```
GET    /api/v1/projects/{project_id}/integrations
POST   /api/v1/projects/{project_id}/integrations
DELETE /api/v1/integrations/{integration_id}
POST   /api/v1/integrations/{integration_id}/sync
```

### 6.9 Webhooks
```
GET    /api/v1/projects/{project_id}/webhooks
POST   /api/v1/projects/{project_id}/webhooks
PUT    /api/v1/webhooks/{webhook_id}
DELETE /api/v1/webhooks/{webhook_id}
GET    /api/v1/webhooks/{webhook_id}/deliveries
```

## 7. UI/UX ТРЕБОВАНИЯ

### 7.1 Страницы приложения

#### 7.1.1 Публичные
- Landing page
- Pricing
- Login/Register
- Password reset
- Email verification

#### 7.1.2 Dashboard
- Overview всех проектов
- Recent audits
- Trending issues
- Quick actions

#### 7.1.3 Проект
- Project overview
- Audit history
- Health score график
- Recent issues
- Team & settings

#### 7.1.4 Аудит
- Progress (real-time)
- Results summary
- Issues по категориям
- Детали страниц
- Сравнение с baseline

#### 7.1.5 Страница детали
- URL и мета
- Issues на странице
- Resources
- Content blocks
- Screenshots (если есть)
- Raw HTML view

#### 7.1.6 Отчеты
- Report builder
- Template selection
- Preview
- Export options
- Schedule setup

#### 7.1.7 Настройки
- Organization settings
- Billing & plan
- Team members
- API keys
- Integrations
- Webhooks

### 7.2 UI компоненты
- Графики health score
- Таблицы с фильтрацией и сортировкой
- Issue cards с severity badges
- Progress bars для аудитов
- Diff viewer для сравнений
- Code highlighter для HTML
- Timeline для истории

### 7.3 Responsive design
- Desktop: полный функционал
- Tablet: адаптивные таблицы
- Mobile: упрощенный view, key metrics

## 8. ПЛАН РАЗВЕРТЫВАНИЯ

### 8.1 Окружения
- **Local**: Docker Compose
- **Dev**: Single server
- **Staging**: Replica of production
- **Production**: Kubernetes cluster

### 8.2 Этапы запуска

#### Phase 1: MVP (2 недели)
- Basic краулинг
- Основные правила
- Simple UI
- PostgreSQL + Redis

#### Phase 2: Core Features (3 недели)
- JS рендеринг
- LLM checks
- Полноценный UI
- API v1

#### Phase 3: Integrations (2 недели)
- Яндекс.Метрика
- Яндекс.Вебмастер
- Export форматы
- Webhooks

#### Phase 4: Enterprise (2 недели)
- Multi-tenancy полная
- Custom rules
- Advanced отчеты
- SLA monitoring

### 8.3 Миграция данных
- Import из CSV
- API для bulk import
- Миграция из конкурентов

## 9. ТЕСТИРОВАНИЕ

### 9.1 Unit тесты
- Coverage > 80%
- Все критичные функции
- Mocking внешних сервисов

### 9.2 Integration тесты
- API endpoints
- Celery tasks
- Database operations
- Cache layer

### 9.3 E2E тесты
- Critical user paths
- Cross-browser
- Mobile testing

### 9.4 Performance тесты
- Load testing (K6/Locust)
- Stress testing
- Database benchmarks
- Crawling limits

### 9.5 Security тесты
- OWASP Top 10
- Dependency scanning
- SQL injection
- XSS/CSRF

## 10. ДОКУМЕНТАЦИЯ

### 10.1 Техническая
- API документация (OpenAPI)
- Deployment guide
- Architecture diagrams
- Database schema

### 10.2 Пользовательская
- Getting started
- User guide
- Video tutorials
- FAQ

### 10.3 Для разработчиков
- Contributing guide
- Code style
- Git workflow
- Testing guide

## 11. MAINTENANCE

### 11.1 Backup
- Database: daily, хранение 30 дней
- Files: S3 versioning
- Configs: Git

### 11.2 Monitoring
- Uptime monitoring
- Performance metrics
- Error tracking (Sentry)
- Log aggregation

### 11.3 Updates
- Security patches: immediate
- Dependencies: monthly
- Features: bi-weekly sprints

## 12. COMPLIANCE И LEGAL

### 12.1 Privacy
- GDPR compliance
- 152-ФЗ compliance
- Cookie policy
- Privacy policy

### 12.2 Security
- SSL/TLS everywhere
- Encryption at rest
- PCI DSS для платежей
- Regular audits

### 12.3 Terms
- Terms of Service
- Acceptable Use Policy
- SLA для paid plans
- Refund policy

## 13. КЛЮЧЕВЫЕ МЕТРИКИ УСПЕХА

### 13.1 Технические
- Uptime > 99.9%
- Crawl speed > 100 pages/min
- API latency < 200ms
- Error rate < 1%

### 13.2 Бизнес
- User retention > 80%
- Paid conversion > 5%
- Churn rate < 10%
- NPS > 40

### 13.3 Использование
- Daily active users
- Audits per user
- Pages analyzed
- Issues fixed rate

## ПРИЛОЖЕНИЯ

### A. Глоссарий
- **Audit** - процесс проверки сайта
- **Baseline** - эталонный аудит для сравнения
- **Chunking** - разбиение контента для LLM
- **Health Score** - интегральная оценка здоровья
- **Issue** - найденная проблема
- **Rule** - правило проверки

### B. Формулы расчета

#### Health Score
```
score = 100
for issue in issues:
    if issue.severity == 'critical':
        score -= 20
    elif issue.severity == 'major':
        score -= 10
    elif issue.severity == 'minor':
        score -= 5
    else:
        score -= 1
score = max(0, score)
```

#### LLM Readiness Score
```
readiness = (
    chunkability * 0.3 +
    answerability * 0.3 +
    entity_coverage * 0.2 +
    fact_consistency * 0.2
)
```

### C. Примеры конфигураций

#### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
    depends_on:
      - db
      - redis
  
  worker:
    build: ./backend
    command: celery worker
    
  scheduler:
    build: ./backend
    command: celery beat
    
  db:
    image: postgres:15
    
  redis:
    image: redis:7
    
  frontend:
    build: ./frontend
```

### D. Примеры API запросов

#### Создание аудита
```bash
curl -X POST https://api.site-health.ru/api/v1/projects/123/audits \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "full",
    "include_rendering": true,
    "max_pages": 500
  }'
```

#### Получение результатов
```bash
curl https://api.site-health.ru/api/v1/audits/456/issues \
  -H "Authorization: Bearer TOKEN"
```

---

## ИТОГО

Полнофункциональный SaaS для аудита сайтов с фокусом на:
1. Комплексную техническую проверку
2. SEO и контент анализ
3. Готовность к нейропоиску (LLM)
4. Мониторинг изменений
5. Интеграции с Яндекс сервисами
6. Гибкую настройку под проект
7. Масштабируемость и надежность

Срок реализации: ~2.5 месяца для полной версии
Команда: 2-3 backend, 1-2 frontend, 1 DevOps
