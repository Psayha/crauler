# Claude Code Setup - Пошаговая инструкция

## Промпт для Claude Code

Используйте этот промпт для начала разработки AI Agency:

```
Я хочу создать AI Agency - автоматизированное цифровое агентство на базе Claude API.

У меня есть 4 документа с полной архитектурой:
1. AGENCY_REQUIREMENTS.md - техническое задание
2. ORCHESTRATOR_IMPLEMENTATION.md - реализация оркестратора
3. AGENTS_PROMPTS.md - промпты для всех агентов
4. CLAUDE_CODE_SETUP.md - эта инструкция

Пожалуйста, начни реализацию с Шага 1 согласно инструкции.
```

## Шаг 1: Инициализация проекта

### 1.1 Создание структуры проекта

```bash
ai-agency/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py
│   │   │   ├── marketing_agent.py
│   │   │   ├── developer_agents.py
│   │   │   ├── analyst_agent.py
│   │   │   ├── ux_agent.py
│   │   │   ├── pm_agent.py
│   │   │   └── qa_agent.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── task.py
│   │   │   └── agent.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── claude_service.py
│   │   │   ├── queue_service.py
│   │   │   └── knowledge_service.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── projects.py
│   │   │   ├── tasks.py
│   │   │   └── agents.py
│   │   └── database/
│   │       ├── __init__.py
│   │       ├── connection.py
│   │       └── migrations/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

### 1.2 Backend Dependencies (requirements.txt)

```txt
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1
redis==5.0.1

# Task Queue
celery==5.3.4
celery[redis]==5.3.4

# AI/ML
anthropic==0.7.0
openai==1.3.0  # for embeddings
langchain==0.0.340
pinecone-client==2.2.4

# Utils
httpx==0.25.2
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
email-validator==2.1.0

# Monitoring
prometheus-fastapi-instrumentator==6.1.0
sentry-sdk==1.38.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

### 1.3 Environment Variables (.env)

```env
# Application
APP_NAME=AI Agency
APP_VERSION=1.0.0
DEBUG=false
SECRET_KEY=your-secret-key-change-this

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_agency
REDIS_URL=redis://localhost:6379

# Claude API
CLAUDE_API_KEY=your-claude-api-key
CLAUDE_MODEL=claude-3-opus-20240229

# Vector Database (Pinecone)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX=ai-agency-knowledge

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Monitoring
SENTRY_DSN=your-sentry-dsn

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Шаг 2: Базовая реализация Backend

### 2.1 Config (app/config.py)

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    app_name: str = "AI Agency"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str
    
    # Database
    database_url: str
    redis_url: str
    
    # Claude API
    claude_api_key: str
    claude_model: str = "claude-3-opus-20240229"
    
    # Vector DB
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    pinecone_index: Optional[str] = None
    
    # Celery
    celery_broker_url: str
    celery_result_backend: str
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### 2.2 Main Application (app/main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database.connection import init_db
from app.api import projects, tasks, agents
from app.services.queue_service import init_celery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Agency...")
    await init_db()
    init_celery()
    yield
    # Shutdown
    logger.info("Shutting down AI Agency...")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 2.3 Claude Service (app/services/claude_service.py)

```python
import anthropic
from typing import Optional, Dict, Any
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.claude_api_key)
        self.model = settings.claude_model
        
    async def send_message(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4000
    ) -> str:
        """
        Send message to Claude API
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    async def parse_json_response(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get JSON response from Claude
        """
        response = await self.send_message(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            **kwargs
        )
        
        try:
            # Clean response and parse JSON
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}\nResponse: {response}")
            raise

claude_service = ClaudeService()
```

## Шаг 3: Реализация Orchestrator

### 3.1 Базовый Orchestrator (app/agents/orchestrator.py)

```python
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
from uuid import uuid4

from app.services.claude_service import claude_service
from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.database.connection import get_db

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
        
    def _load_system_prompt(self) -> str:
        # Загружаем из AGENTS_PROMPTS.md
        return """You are the CEO and Chief Orchestrator of an AI Agency..."""
    
    async def create_project(self, request: str, organization_id: str) -> Project:
        """
        Create new project from request
        """
        # Analyze request
        analysis = await self._analyze_request(request)
        
        # Create project in database
        async with get_db() as db:
            project = Project(
                id=str(uuid4()),
                organization_id=organization_id,
                name=analysis['project_name'],
                description=request,
                type=analysis['project_type'],
                status=ProjectStatus.PLANNING,
                metadata=analysis
            )
            db.add(project)
            await db.commit()
            
        # Decompose into tasks
        tasks = await self._decompose_project(project)
        
        # Save tasks
        await self._save_tasks(tasks, project.id)
        
        return project
    
    async def _analyze_request(self, request: str) -> Dict[str, Any]:
        """
        Analyze project request
        """
        prompt = f"""
        Analyze this project request:
        {request}
        
        Provide JSON with:
        - project_name: suggested name
        - project_type: website|mobile_app|marketing|data_analysis|custom
        - complexity: simple|moderate|complex
        - estimated_hours: number
        - required_agents: list of agents needed
        - key_requirements: main requirements
        - risks: potential risks
        """
        
        return await claude_service.parse_json_response(
            system_prompt=self.system_prompt,
            user_prompt=prompt
        )

orchestrator = OrchestratorAgent()
```

## Шаг 4: API Endpoints

### 4.1 Projects API (app/api/projects.py)

```python
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel

from app.agents.orchestrator import orchestrator
from app.models.project import Project

router = APIRouter()

class ProjectCreateRequest(BaseModel):
    description: str
    organization_id: str

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str
    type: str

@router.post("/", response_model=ProjectResponse)
async def create_project(request: ProjectCreateRequest):
    """
    Create new project
    """
    try:
        project = await orchestrator.create_project(
            request=request.description,
            organization_id=request.organization_id
        )
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            type=project.type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}")
async def get_project(project_id: str):
    """
    Get project details
    """
    # Implementation here
    pass

@router.post("/{project_id}/execute")
async def execute_project(project_id: str):
    """
    Start project execution
    """
    # Implementation here
    pass
```

## Шаг 5: Frontend Setup

### 5.1 Next.js Project Structure

```bash
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── projects/
│   │   ├── page.tsx
│   │   └── [id]/
│   │       └── page.tsx
│   └── api/
├── components/
│   ├── project-form.tsx
│   ├── project-list.tsx
│   ├── task-board.tsx
│   └── agent-status.tsx
├── lib/
│   ├── api-client.ts
│   └── types.ts
└── package.json
```

### 5.2 Package.json

```json
{
  "name": "ai-agency-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.0.4",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-select": "^2.0.0",
    "@tanstack/react-query": "^5.8.0",
    "axios": "^1.6.2",
    "tailwindcss": "^3.3.6",
    "shadcn-ui": "latest",
    "zustand": "^4.4.7"
  }
}
```

## Шаг 6: Docker Setup

### 6.1 docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ai_agency
      POSTGRES_USER: aiagency
      POSTGRES_PASSWORD: securepassword
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://aiagency:securepassword@postgres:5432/ai_agency
      REDIS_URL: redis://redis:6379
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --reload --host 0.0.0.0
  
  celery:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://aiagency:securepassword@postgres:5432/ai_agency
      REDIS_URL: redis://redis:6379
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
    depends_on:
      - postgres
      - redis
    command: celery -A app.celery_app worker --loglevel=info
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app

volumes:
  postgres_data:
```

## Шаг 7: Запуск и тестирование

### 7.1 Первый запуск

```bash
# 1. Клонирование и setup
git init ai-agency
cd ai-agency

# 2. Создание .env файла
cp .env.example .env
# Заполните CLAUDE_API_KEY и другие переменные

# 3. Запуск Docker
docker-compose up -d

# 4. Миграции БД
docker-compose exec backend alembic upgrade head

# 5. Открыть браузер
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### 7.2 Тестовый проект

```python
# Создание тестового проекта через API
import requests

response = requests.post("http://localhost:8000/api/projects", json={
    "description": "Create a landing page for AI consulting company with contact form and blog",
    "organization_id": "test-org-123"
})

project = response.json()
print(f"Created project: {project['id']}")

# Запуск выполнения
execute_response = requests.post(
    f"http://localhost:8000/api/projects/{project['id']}/execute"
)
```

## Шаг 8: Расширение функционала

### 8.1 Добавление новых агентов

1. Создайте файл агента в `backend/app/agents/`
2. Добавьте промпт в AGENTS_PROMPTS.md
3. Зарегистрируйте в AgentRegistry
4. Обновите Orchestrator для использования

### 8.2 Добавление workflows

1. Создайте workflow в `backend/app/workflows/`
2. Определите последовательность задач
3. Интегрируйте с Orchestrator

### 8.3 Интеграции

- GitHub: Автоматические PR
- Slack: Уведомления
- Stripe: Платежи

## Шаг 9: Production Deployment

### 9.1 Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-agency-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-agency-backend
  template:
    metadata:
      labels:
        app: ai-agency-backend
    spec:
      containers:
      - name: backend
        image: ai-agency/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: CLAUDE_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-agency-secrets
              key: claude-api-key
```

### 9.2 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push Docker images
        run: |
          docker build -t ai-agency/backend:latest ./backend
          docker build -t ai-agency/frontend:latest ./frontend
          docker push ai-agency/backend:latest
          docker push ai-agency/frontend:latest
      
      - name: Deploy to Kubernetes
        run: |
          kubectl apply -f k8s/
          kubectl rollout status deployment/ai-agency-backend
```

## Шаг 10: Мониторинг и оптимизация

### 10.1 Prometheus метрики

```python
# backend/app/monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Метрики
project_counter = Counter('ai_agency_projects_total', 'Total number of projects')
task_counter = Counter('ai_agency_tasks_total', 'Total tasks', ['agent_type', 'status'])
token_usage = Counter('ai_agency_tokens_total', 'Total tokens used', ['agent_type'])
task_duration = Histogram('ai_agency_task_duration_seconds', 'Task execution time', ['agent_type'])
active_agents = Gauge('ai_agency_active_agents', 'Number of active agents', ['agent_type'])

class MetricsCollector:
    @staticmethod
    def track_project_created():
        project_counter.inc()
    
    @staticmethod
    def track_task_completed(agent_type: str, duration: float, tokens: int):
        task_counter.labels(agent_type=agent_type, status='completed').inc()
        task_duration.labels(agent_type=agent_type).observe(duration)
        token_usage.labels(agent_type=agent_type).inc(tokens)
    
    @staticmethod
    def update_active_agents(agent_type: str, count: int):
        active_agents.labels(agent_type=agent_type).set(count)
```

### 10.2 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "AI Agency Monitoring",
    "panels": [
      {
        "title": "Projects Created",
        "targets": [
          {
            "expr": "rate(ai_agency_projects_total[5m])"
          }
        ]
      },
      {
        "title": "Task Success Rate",
        "targets": [
          {
            "expr": "rate(ai_agency_tasks_total{status='completed'}[5m]) / rate(ai_agency_tasks_total[5m])"
          }
        ]
      },
      {
        "title": "Token Usage by Agent",
        "targets": [
          {
            "expr": "sum by (agent_type) (rate(ai_agency_tokens_total[1h]))"
          }
        ]
      },
      {
        "title": "Average Task Duration",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(ai_agency_task_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

### 10.3 Логирование и трейсинг

```python
# backend/app/logging_config.py
import logging
import json
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['logger'] = record.name

def setup_logging():
    logHandler = logging.StreamHandler()
    formatter = CustomJsonFormatter()
    logHandler.setFormatter(formatter)
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logHandler]
    )
    
    # Отправка в ELK Stack
    if settings.elk_enabled:
        from pythonjsonlogger import logstash
        logstash_handler = logstash.LogstashHandler(
            host=settings.logstash_host,
            port=settings.logstash_port,
            version=1
        )
        logging.getLogger().addHandler(logstash_handler)
```

## Шаг 11: Оптимизация производительности

### 11.1 Кэширование результатов

```python
# backend/app/cache.py
import redis
import json
import hashlib
from typing import Optional, Any
from datetime import timedelta

class CacheManager:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)
        
    def _generate_key(self, prefix: str, data: dict) -> str:
        """Generate cache key from data"""
        data_str = json.dumps(data, sort_keys=True)
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    async def get_cached_agent_response(
        self, 
        agent_type: str, 
        prompt: str
    ) -> Optional[dict]:
        """Get cached agent response"""
        key = self._generate_key(f"agent:{agent_type}", {"prompt": prompt})
        cached = self.redis_client.get(key)
        
        if cached:
            return json.loads(cached)
        return None
    
    async def cache_agent_response(
        self,
        agent_type: str,
        prompt: str,
        response: dict,
        ttl: int = 3600
    ):
        """Cache agent response"""
        key = self._generate_key(f"agent:{agent_type}", {"prompt": prompt})
        self.redis_client.setex(
            key,
            timedelta(seconds=ttl),
            json.dumps(response)
        )

cache_manager = CacheManager()
```

### 11.2 Параллельное выполнение задач

```python
# backend/app/execution/parallel_executor.py
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class ParallelExecutor:
    def __init__(self, max_workers: int = 5):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    async def execute_parallel_tasks(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute independent tasks in parallel"""
        
        # Группировка задач по зависимостям
        independent_tasks = [t for t in tasks if not t.get('dependencies')]
        dependent_tasks = [t for t in tasks if t.get('dependencies')]
        
        # Выполнение независимых задач параллельно
        results = []
        if independent_tasks:
            futures = []
            
            for task in independent_tasks:
                future = asyncio.create_task(
                    self._execute_single_task(task)
                )
                futures.append(future)
            
            # Ждем завершения всех задач
            completed = await asyncio.gather(*futures, return_exceptions=True)
            
            for i, result in enumerate(completed):
                if isinstance(result, Exception):
                    logger.error(f"Task failed: {independent_tasks[i]['id']}: {result}")
                    results.append({
                        'task_id': independent_tasks[i]['id'],
                        'status': 'failed',
                        'error': str(result)
                    })
                else:
                    results.append(result)
        
        # Последовательное выполнение зависимых задач
        for task in dependent_tasks:
            await self._wait_for_dependencies(task['dependencies'], results)
            result = await self._execute_single_task(task)
            results.append(result)
        
        return results
    
    async def _execute_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task"""
        agent_type = task['agent_type']
        
        # Получение агента
        agent = self._get_agent(agent_type)
        
        # Выполнение
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await agent.execute(task)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return {
                'task_id': task['id'],
                'status': 'completed',
                'result': result,
                'execution_time': execution_time,
                'agent_type': agent_type
            }
        except Exception as e:
            logger.error(f"Task execution failed: {task['id']}: {e}")
            raise

parallel_executor = ParallelExecutor()
```

### 11.3 Token оптимизация

```python
# backend/app/optimization/token_optimizer.py
import tiktoken
from typing import List, Dict, Any
import re

class TokenOptimizer:
    def __init__(self):
        self.encoder = tiktoken.encoding_for_model("gpt-4")
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoder.encode(text))
    
    def optimize_prompt(self, prompt: str, max_tokens: int = 2000) -> str:
        """Optimize prompt to fit within token limit"""
        current_tokens = self.count_tokens(prompt)
        
        if current_tokens <= max_tokens:
            return prompt
        
        # Стратегии оптимизации
        optimized = prompt
        
        # 1. Удаление лишних пробелов
        optimized = re.sub(r'\s+', ' ', optimized)
        
        # 2. Сокращение повторяющихся инструкций
        optimized = self._remove_duplicates(optimized)
        
        # 3. Компрессия примеров
        optimized = self._compress_examples(optimized)
        
        # 4. Если все еще слишком длинно - обрезка
        if self.count_tokens(optimized) > max_tokens:
            optimized = self._truncate_to_limit(optimized, max_tokens)
        
        return optimized
    
    def _compress_examples(self, text: str) -> str:
        """Compress examples in prompt"""
        # Находим примеры и оставляем только первый
        pattern = r'Example \d+:.*?(?=Example \d+:|$)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        if len(matches) > 2:
            # Оставляем только первые 2 примера
            compressed = text
            for match in matches[2:]:
                compressed = compressed.replace(match, '')
            return compressed
        
        return text
    
    def batch_prompts(
        self,
        tasks: List[Dict[str, Any]],
        max_batch_tokens: int = 8000
    ) -> List[List[Dict[str, Any]]]:
        """Batch multiple prompts for efficient processing"""
        batches = []
        current_batch = []
        current_tokens = 0
        
        for task in tasks:
            task_tokens = self.count_tokens(task.get('prompt', ''))
            
            if current_tokens + task_tokens > max_batch_tokens:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [task]
                current_tokens = task_tokens
            else:
                current_batch.append(task)
                current_tokens += task_tokens
        
        if current_batch:
            batches.append(current_batch)
        
        return batches

token_optimizer = TokenOptimizer()
```

## Шаг 12: Тестирование

### 12.1 Unit тесты

```python
# backend/tests/test_orchestrator.py
import pytest
from unittest.mock import Mock, patch
from app.agents.orchestrator import OrchestratorAgent

@pytest.fixture
def orchestrator():
    return OrchestratorAgent()

@pytest.fixture
def mock_claude_service():
    with patch('app.agents.orchestrator.claude_service') as mock:
        yield mock

@pytest.mark.asyncio
async def test_analyze_request(orchestrator, mock_claude_service):
    """Test project request analysis"""
    
    # Setup
    request = "Create a landing page for my startup"
    mock_response = {
        "project_name": "Startup Landing Page",
        "project_type": "website",
        "complexity": "simple",
        "estimated_hours": 8,
        "required_agents": ["ux_designer", "frontend_developer"],
        "key_requirements": ["responsive design", "contact form"],
        "risks": ["unclear branding guidelines"]
    }
    
    mock_claude_service.parse_json_response.return_value = mock_response
    
    # Execute
    result = await orchestrator._analyze_request(request)
    
    # Assert
    assert result["project_type"] == "website"
    assert "ux_designer" in result["required_agents"]
    assert result["estimated_hours"] == 8

@pytest.mark.asyncio
async def test_task_decomposition(orchestrator, mock_claude_service):
    """Test project decomposition into tasks"""
    
    # Setup
    project = Mock(
        id="test-project",
        description="Create landing page",
        project_type="website",
        requirements=["responsive", "fast"]
    )
    
    mock_response = {
        "tasks": [
            {
                "title": "Design wireframes",
                "agent_type": "ux_designer",
                "dependencies": [],
                "estimated_tokens": 1000
            },
            {
                "title": "Implement frontend",
                "agent_type": "frontend_developer",
                "dependencies": [0],
                "estimated_tokens": 2000
            }
        ]
    }
    
    mock_claude_service.parse_json_response.return_value = mock_response
    
    # Execute
    tasks = await orchestrator._decompose_project(project)
    
    # Assert
    assert len(tasks) == 2
    assert tasks[0].agent_type == "ux_designer"
    assert tasks[1].dependencies == ["Design wireframes"]
```

### 12.2 Integration тесты

```python
# backend/tests/test_integration.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_project_flow():
    """Test complete project creation flow"""
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create project
        response = await client.post("/api/projects", json={
            "description": "Build a todo app with React",
            "organization_id": "test-org"
        })
        
        assert response.status_code == 200
        project = response.json()
        assert project["id"]
        assert project["status"] == "planning"
        
        # Get project tasks
        tasks_response = await client.get(f"/api/projects/{project['id']}/tasks")
        assert tasks_response.status_code == 200
        
        tasks = tasks_response.json()
        assert len(tasks) > 0
        
        # Execute project
        exec_response = await client.post(f"/api/projects/{project['id']}/execute")
        assert exec_response.status_code == 200

@pytest.mark.asyncio
async def test_agent_communication():
    """Test inter-agent communication"""
    
    # Setup agents
    marketing_agent = MarketingAgent()
    developer_agent = DeveloperAgent()
    
    # Send message
    message = {
        "from_agent": "marketing",
        "to_agent": "developer",
        "type": "request",
        "content": {
            "action": "need_technical_feasibility",
            "data": {"feature": "real-time chat"}
        }
    }
    
    response = await developer_agent.handle_message(message)
    
    assert response["type"] == "response"
    assert "feasibility" in response["content"]
```

### 12.3 Load тестирование

```python
# backend/tests/load_test.py
import asyncio
import aiohttp
import time
from typing import List

async def create_project(session: aiohttp.ClientSession, index: int):
    """Create a single project"""
    start = time.time()
    
    data = {
        "description": f"Test project {index}",
        "organization_id": "load-test"
    }
    
    async with session.post(
        "http://localhost:8000/api/projects",
        json=data
    ) as response:
        result = await response.json()
        duration = time.time() - start
        
        return {
            "index": index,
            "project_id": result.get("id"),
            "duration": duration,
            "status": response.status
        }

async def run_load_test(concurrent_requests: int = 10):
    """Run load test"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for i in range(concurrent_requests):
            task = create_project(session, i)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Анализ результатов
        successful = [r for r in results if r["status"] == 200]
        avg_duration = sum(r["duration"] for r in results) / len(results)
        
        print(f"Total requests: {concurrent_requests}")
        print(f"Successful: {len(successful)}")
        print(f"Average duration: {avg_duration:.2f}s")
        print(f"Requests per second: {concurrent_requests / avg_duration:.2f}")

if __name__ == "__main__":
    asyncio.run(run_load_test(50))
```

## Шаг 13: Дополнительные агенты и функции

### 13.1 Legal Advisor Agent

```python
# backend/app/agents/legal_agent.py
class LegalAdvisorAgent:
    def __init__(self):
        self.system_prompt = LEGAL_ADVISOR_PROMPT
        
    async def generate_terms_of_service(self, company_info: dict) -> str:
        """Generate Terms of Service"""
        prompt = f"""
        Generate Terms of Service for:
        Company: {company_info['name']}
        Type: {company_info['type']}
        Services: {company_info['services']}
        
        Include sections:
        1. Acceptance of Terms
        2. Description of Service
        3. User Responsibilities
        4. Intellectual Property
        5. Privacy
        6. Disclaimers
        7. Limitation of Liability
        8. Termination
        9. Governing Law
        """
        
        return await claude_service.send_message(
            system_prompt=self.system_prompt,
            user_prompt=prompt
        )
```

### 13.2 Financial Analyst Agent

```python
# backend/app/agents/financial_agent.py
class FinancialAnalystAgent:
    def __init__(self):
        self.system_prompt = FINANCIAL_ANALYST_PROMPT
        
    async def analyze_project_roi(self, project_data: dict) -> dict:
        """Analyze project ROI"""
        prompt = f"""
        Analyze ROI for project:
        Investment: ${project_data['investment']}
        Expected Revenue: ${project_data['expected_revenue']}
        Timeline: {project_data['timeline_months']} months
        
        Calculate:
        1. ROI percentage
        2. Payback period
        3. Net Present Value (NPV)
        4. Risk assessment
        5. Recommendations
        """
        
        return await claude_service.parse_json_response(
            system_prompt=self.system_prompt,
            user_prompt=prompt
        )
```

## Финальные рекомендации

### Приоритеты разработки

1. **Фаза 1 (MVP)**: Базовый orchestrator + 3 агента
2. **Фаза 2**: Полный набор агентов + UI
3. **Фаза 3**: Оптимизации и масштабирование
4. **Фаза 4**: Marketplace и кастомизация

### Ключевые метрики успеха

- Task completion rate > 95%
- Average project time < 24 hours
- Token cost per project < $10
- Customer satisfaction > 4.5/5

### Советы по запуску

1. Начните с простых проектов
2. Собирайте feedback активно
3. Итерируйте промпты на основе результатов
4. Мониторьте costs внимательно
5. Автоматизируйте все что можно

Удачи в создании вашего AI Agency! 🚀
