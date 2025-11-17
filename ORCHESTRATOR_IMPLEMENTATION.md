# Orchestrator Agent - Детальная реализация

## 1. Архитектура Orchestrator

### 1.1 Основной класс

```python
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from uuid import uuid4

class ProjectType(Enum):
    WEBSITE = "website"
    MOBILE_APP = "mobile_app"
    MARKETING_CAMPAIGN = "marketing_campaign"
    DATA_ANALYSIS = "data_analysis"
    CONTENT_CREATION = "content_creation"
    CUSTOM = "custom"

class TaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class ProjectContext:
    """Контекст проекта для принятия решений"""
    project_id: str
    project_type: ProjectType
    description: str
    requirements: Dict[str, Any]
    constraints: Dict[str, Any]
    deadline: Optional[datetime]
    budget_tokens: int
    priority: TaskPriority
    metadata: Dict[str, Any]

@dataclass
class TaskDefinition:
    """Определение задачи для агента"""
    task_id: str
    project_id: str
    agent_type: str
    title: str
    description: str
    input_data: Dict[str, Any]
    dependencies: List[str]
    priority: TaskPriority
    estimated_tokens: int
    deadline: Optional[datetime]

class OrchestratorAgent:
    """
    Главный координатор AI Agency
    Управляет всем жизненным циклом проектов
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.claude_client = ClaudeAPIClient(config['claude_api_key'])
        self.db = DatabaseManager(config['database'])
        self.queue = TaskQueueManager(config['redis'])
        self.knowledge_base = KnowledgeBase(config['vector_db'])
        self.agent_registry = AgentRegistry()
        
        # Состояние оркестратора
        self.active_projects: Dict[str, ProjectContext] = {}
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_id
        self.performance_metrics: Dict[str, Any] = {}
        
        # System prompt для оркестратора
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Создание system prompt для оркестратора"""
        return """You are the CEO and Chief Orchestrator of an AI Agency.
        
Your role is to:
1. Analyze incoming project requests and understand their full scope
2. Decompose projects into specific, actionable tasks
3. Assign tasks to the most suitable specialist agents
4. Monitor progress and ensure quality standards
5. Integrate results into cohesive deliverables
6. Maintain communication with stakeholders

You have the following specialist agents at your disposal:
- Marketing Agent: Marketing strategies, content planning, SEO/SEM
- Frontend Developer: React, Vue, UI/UX implementation
- Backend Developer: APIs, databases, business logic
- Mobile Developer: iOS/Android applications
- DevOps Engineer: Infrastructure, deployment, CI/CD
- Data Analyst: Data analysis, reporting, insights
- UX Designer: User research, wireframes, prototypes
- Project Manager: Sprint planning, task tracking
- QA Engineer: Testing, quality assurance
- Content Writer: Blog posts, documentation, copy

Decision Framework:
- Prioritize tasks by impact and dependencies
- Optimize for parallel execution where possible
- Ensure quality gates at each stage
- Balance speed with thoroughness
- Consider token budget constraints

Output Format:
Always structure your responses as JSON with clear action items and rationale."""

    async def analyze_project(self, request: str) -> ProjectContext:
        """
        Анализ входящего запроса и создание контекста проекта
        """
        analysis_prompt = f"""Analyze this project request and provide a structured breakdown:

Request: {request}

Provide a JSON response with:
1. project_type: One of [website, mobile_app, marketing_campaign, data_analysis, content_creation, custom]
2. complexity: One of [simple, moderate, complex, enterprise]
3. estimated_hours: Number
4. required_agents: List of agent types needed
5. key_requirements: List of main requirements
6. potential_risks: List of risks
7. success_criteria: List of measurable outcomes
8. recommended_approach: Brief strategy"""

        response = await self.claude_client.send_message(
            system_prompt=self.system_prompt,
            user_prompt=analysis_prompt,
            temperature=0.3
        )
        
        analysis = json.loads(response)
        
        # Создание контекста проекта
        project_context = ProjectContext(
            project_id=str(uuid4()),
            project_type=ProjectType(analysis['project_type']),
            description=request,
            requirements=analysis['key_requirements'],
            constraints={
                'complexity': analysis['complexity'],
                'estimated_hours': analysis['estimated_hours']
            },
            deadline=self._calculate_deadline(analysis['estimated_hours']),
            budget_tokens=self._estimate_token_budget(analysis['complexity']),
            priority=self._determine_priority(analysis),
            metadata=analysis
        )
        
        # Сохранение в БД
        await self.db.save_project(project_context)
        self.active_projects[project_context.project_id] = project_context
        
        return project_context

    async def decompose_project(self, project: ProjectContext) -> List[TaskDefinition]:
        """
        Декомпозиция проекта на конкретные задачи
        """
        decomposition_prompt = f"""Decompose this project into specific tasks:

Project Type: {project.project_type.value}
Description: {project.description}
Requirements: {json.dumps(project.requirements, indent=2)}
Constraints: {json.dumps(project.constraints, indent=2)}

Create a detailed task breakdown with:
1. tasks: Array of task objects, each containing:
   - title: Clear task title
   - description: Detailed description
   - agent_type: Which agent should handle this
   - dependencies: Array of task indices this depends on
   - estimated_tokens: Estimated Claude API tokens
   - deliverables: Expected outputs
   - acceptance_criteria: How to verify completion
2. execution_order: Optimal sequence considering dependencies
3. parallel_groups: Tasks that can run simultaneously
4. critical_path: Tasks that directly impact timeline

Ensure tasks are specific, measurable, and assignable to individual agents."""

        response = await self.claude_client.send_message(
            system_prompt=self.system_prompt,
            user_prompt=decomposition_prompt,
            temperature=0.2
        )
        
        decomposition = json.loads(response)
        tasks = []
        
        for idx, task_data in enumerate(decomposition['tasks']):
            task = TaskDefinition(
                task_id=str(uuid4()),
                project_id=project.project_id,
                agent_type=task_data['agent_type'],
                title=task_data['title'],
                description=task_data['description'],
                input_data={
                    'requirements': task_data.get('deliverables', []),
                    'criteria': task_data.get('acceptance_criteria', []),
                    'context': project.requirements
                },
                dependencies=[decomposition['tasks'][i]['title'] 
                            for i in task_data.get('dependencies', [])],
                priority=self._calculate_task_priority(task_data, decomposition),
                estimated_tokens=task_data['estimated_tokens'],
                deadline=self._calculate_task_deadline(project, task_data)
            )
            tasks.append(task)
            
            # Сохранение в БД
            await self.db.save_task(task)
        
        # Анализ критического пути
        await self._analyze_critical_path(tasks, decomposition)
        
        return tasks

    async def assign_tasks(self, tasks: List[TaskDefinition]) -> Dict[str, str]:
        """
        Распределение задач между агентами
        """
        assignments = {}
        
        for task in tasks:
            # Проверка доступности агента
            agent_status = await self.agent_registry.get_agent_status(task.agent_type)
            
            if agent_status['available']:
                # Назначение задачи
                agent_id = await self.agent_registry.assign_task(
                    agent_type=task.agent_type,
                    task_id=task.task_id
                )
                
                assignments[task.task_id] = agent_id
                self.task_assignments[task.task_id] = agent_id
                
                # Добавление в очередь
                await self.queue.enqueue_task(
                    task_id=task.task_id,
                    agent_id=agent_id,
                    priority=task.priority.value,
                    data=task.dict()
                )
                
                # Логирование
                await self._log_assignment(task, agent_id)
            else:
                # Добавление в очередь ожидания
                await self.queue.add_to_waiting_queue(task)
        
        return assignments

    async def monitor_execution(self, project_id: str):
        """
        Мониторинг выполнения проекта
        """
        project = self.active_projects.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        while True:
            # Получение статуса всех задач
            tasks = await self.db.get_project_tasks(project_id)
            
            completed = 0
            in_progress = 0
            blocked = 0
            failed = 0
            
            for task in tasks:
                if task['status'] == TaskStatus.COMPLETED.value:
                    completed += 1
                elif task['status'] == TaskStatus.IN_PROGRESS.value:
                    in_progress += 1
                elif task['status'] == TaskStatus.BLOCKED.value:
                    blocked += 1
                elif task['status'] == TaskStatus.FAILED.value:
                    failed += 1
            
            # Обработка заблокированных задач
            if blocked > 0:
                await self._handle_blocked_tasks(project_id)
            
            # Обработка неудачных задач
            if failed > 0:
                await self._handle_failed_tasks(project_id)
            
            # Проверка завершения
            if completed == len(tasks):
                await self._finalize_project(project_id)
                break
            
            # Обновление метрик
            await self._update_metrics(project_id, {
                'completed': completed,
                'in_progress': in_progress,
                'blocked': blocked,
                'failed': failed,
                'progress_percentage': (completed / len(tasks)) * 100
            })
            
            # Ждем перед следующей проверкой
            await asyncio.sleep(10)

    async def integrate_results(self, project_id: str) -> Dict[str, Any]:
        """
        Интеграция результатов всех задач в финальный результат
        """
        project = self.active_projects.get(project_id)
        tasks = await self.db.get_project_tasks(project_id)
        
        integration_prompt = f"""Integrate the results from all tasks into a cohesive deliverable:

Project: {project.description}
Project Type: {project.project_type.value}

Task Results:
{json.dumps([{
    'task': task['title'],
    'agent': task['assigned_agent'],
    'result': task['output_data']
} for task in tasks], indent=2)}

Create an integrated deliverable with:
1. executive_summary: High-level overview
2. key_deliverables: Main outputs organized by category
3. technical_details: Detailed technical information
4. next_steps: Recommended actions
5. success_metrics: How to measure success
6. appendix: Supporting materials

Ensure the output is cohesive, professional, and ready for client delivery."""

        response = await self.claude_client.send_message(
            system_prompt=self.system_prompt,
            user_prompt=integration_prompt,
            temperature=0.3
        )
        
        integrated_result = json.loads(response)
        
        # Сохранение финального результата
        await self.db.save_project_deliverable(project_id, integrated_result)
        
        # Генерация артефактов
        artifacts = await self._generate_artifacts(project_id, integrated_result)
        
        return {
            'project_id': project_id,
            'deliverable': integrated_result,
            'artifacts': artifacts,
            'metrics': await self._get_project_metrics(project_id)
        }

    async def handle_agent_communication(self, message: Dict[str, Any]):
        """
        Обработка межагентной коммуникации
        """
        msg_type = message['message_type']
        
        if msg_type == 'request':
            await self._handle_agent_request(message)
        elif msg_type == 'update':
            await self._handle_agent_update(message)
        elif msg_type == 'error':
            await self._handle_agent_error(message)
        elif msg_type == 'clarification':
            await self._handle_clarification_request(message)

    async def _handle_agent_request(self, message: Dict[str, Any]):
        """
        Обработка запроса от агента
        """
        request_type = message['content']['action']
        
        if request_type == 'need_context':
            # Агенту нужен дополнительный контекст
            context = await self.knowledge_base.get_context(
                project_id=message['subject'],
                query=message['content']['data']['query']
            )
            await self._send_to_agent(
                agent_id=message['from_agent'],
                content={'context': context}
            )
            
        elif request_type == 'need_review':
            # Агент запрашивает review
            review_result = await self._review_agent_work(
                task_id=message['subject'],
                work=message['content']['data']
            )
            await self._send_to_agent(
                agent_id=message['from_agent'],
                content={'review': review_result}
            )

    async def optimize_performance(self):
        """
        Оптимизация производительности системы
        """
        # Анализ метрик производительности
        metrics = await self.db.get_performance_metrics()
        
        optimization_prompt = f"""Analyze system performance and suggest optimizations:

Current Metrics:
{json.dumps(metrics, indent=2)}

Provide recommendations for:
1. agent_utilization: How to better distribute work
2. token_efficiency: How to reduce token usage
3. task_parallelization: Which tasks can run simultaneously
4. bottlenecks: Identify and address bottlenecks
5. prompt_optimization: Suggestions for better prompts"""

        response = await self.claude_client.send_message(
            system_prompt=self.system_prompt,
            user_prompt=optimization_prompt,
            temperature=0.4
        )
        
        optimizations = json.loads(response)
        
        # Применение оптимизаций
        await self._apply_optimizations(optimizations)

    # Вспомогательные методы
    
    def _calculate_deadline(self, estimated_hours: int) -> datetime:
        """Расчет дедлайна на основе оценки часов"""
        return datetime.now() + timedelta(hours=estimated_hours * 1.5)
    
    def _estimate_token_budget(self, complexity: str) -> int:
        """Оценка бюджета токенов на основе сложности"""
        budgets = {
            'simple': 50000,
            'moderate': 150000,
            'complex': 300000,
            'enterprise': 500000
        }
        return budgets.get(complexity, 100000)
    
    def _determine_priority(self, analysis: Dict) -> TaskPriority:
        """Определение приоритета проекта"""
        if analysis.get('urgent', False):
            return TaskPriority.CRITICAL
        elif analysis['complexity'] == 'enterprise':
            return TaskPriority.HIGH
        else:
            return TaskPriority.NORMAL

    async def _handle_blocked_tasks(self, project_id: str):
        """Обработка заблокированных задач"""
        blocked_tasks = await self.db.get_blocked_tasks(project_id)
        
        for task in blocked_tasks:
            # Проверка, разрешены ли зависимости
            deps_resolved = await self._check_dependencies_resolved(task['dependencies'])
            
            if deps_resolved:
                # Разблокировка и переназначение
                await self.db.update_task_status(task['id'], TaskStatus.PENDING)
                await self.assign_tasks([task])

    async def _handle_failed_tasks(self, project_id: str):
        """Обработка неудачных задач"""
        failed_tasks = await self.db.get_failed_tasks(project_id)
        
        for task in failed_tasks:
            # Анализ причины сбоя
            failure_reason = await self._analyze_failure(task)
            
            if failure_reason['retryable']:
                # Повторная попытка
                await self.queue.enqueue_task(
                    task_id=task['id'],
                    agent_id=task['assigned_agent'],
                    priority=TaskPriority.HIGH.value,
                    data=task
                )
            else:
                # Эскалация
                await self._escalate_failure(task, failure_reason)
