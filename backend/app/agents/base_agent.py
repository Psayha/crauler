from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
import time
from datetime import datetime

from app.services.claude_service import claude_service
from app.services.knowledge_service import knowledge_service
from app.models.task import Task
from app.models.agent_execution import AgentExecution
from app.database.connection import get_db

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all specialized agents
    Each agent has a specific expertise and system prompt
    """

    def __init__(self):
        self.agent_type = self.get_agent_type()
        self.system_prompt = self.get_system_prompt()
        self.temperature = self.get_temperature()

    @abstractmethod
    def get_agent_type(self) -> str:
        """Return agent type identifier"""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return system prompt for this agent"""
        pass

    def get_temperature(self) -> float:
        """Return temperature for Claude API calls (0-1)"""
        return 0.3  # Default conservative temperature

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent

        Args:
            task: Task object from database

        Returns:
            Execution result with deliverables
        """
        logger.info(f"{self.agent_type} executing task: {task.title}")

        start_time = time.time()

        try:
            # Fetch relevant context from Knowledge Base
            kb_context = await self._fetch_relevant_context(task)

            # Build task prompt with context
            user_prompt = self._build_task_prompt(task, kb_context)

            # Call Claude API
            response = await claude_service.parse_json_response(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature,
                max_tokens=4000,
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Save execution to database
            async with get_db() as db:
                execution = AgentExecution(
                    task_id=task.id,
                    agent_type=self.agent_type,
                    prompt=user_prompt,
                    response=str(response),
                    tokens_used=claude_service.count_tokens(user_prompt)
                    + claude_service.count_tokens(str(response)),
                    execution_time_ms=execution_time_ms,
                    status="completed",
                    execution_metadata={
                        "temperature": self.temperature,
                        "task_title": task.title,
                    },
                )
                db.add(execution)

                # Update task
                task.output_data = response
                task.actual_tokens = execution.tokens_used
                task.completed_at = datetime.utcnow()

            logger.info(
                f"{self.agent_type} completed task {task.id} in {execution_time_ms}ms"
            )

            return {
                "status": "success",
                "agent": self.agent_type,
                "task_id": str(task.id),
                "result": response,
                "execution_time_ms": execution_time_ms,
                "tokens_used": execution.tokens_used,
            }

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"{self.agent_type} failed task {task.id}: {e}")

            # Save failed execution
            async with get_db() as db:
                execution = AgentExecution(
                    task_id=task.id,
                    agent_type=self.agent_type,
                    prompt=user_prompt if "user_prompt" in locals() else "",
                    status="failed",
                    error_message=str(e),
                    execution_time_ms=execution_time_ms,
                )
                db.add(execution)

            return {
                "status": "failed",
                "agent": self.agent_type,
                "task_id": str(task.id),
                "error": str(e),
                "execution_time_ms": execution_time_ms,
            }

    async def execute(self, prompt: str) -> str:
        """
        Execute a direct prompt without task context.
        Used for meta-operations like HR Agent analysis.

        Args:
            prompt: Direct user prompt

        Returns:
            Claude's response text
        """
        try:
            response = await claude_service.send_message(
                system_prompt=self.system_prompt,
                user_prompt=prompt,
                temperature=self.temperature,
                max_tokens=4000,
            )
            return response
        except Exception as e:
            logger.error(f"{self.agent_type} execution failed: {e}")
            raise

    def _build_task_prompt(self, task: Task, kb_context: str = "") -> str:
        """
        Build task prompt from task data

        Args:
            task: Task object
            kb_context: Relevant context from Knowledge Base

        Returns:
            Formatted prompt for Claude
        """
        prompt = f"""Task: {task.title}

Description:
{task.description}

"""

        # Add input data if available
        if task.input_data:
            if task.input_data.get("deliverables"):
                prompt += f"""Expected Deliverables:
{chr(10).join(f'- {d}' for d in task.input_data['deliverables'])}

"""

            if task.input_data.get("acceptance_criteria"):
                prompt += f"""Acceptance Criteria:
{chr(10).join(f'- {c}' for c in task.input_data['acceptance_criteria'])}

"""

            if task.input_data.get("project_context"):
                context = task.input_data["project_context"]
                prompt += f"""Project Context:
- Type: {context.get('project_type', 'unknown')}
- Complexity: {context.get('complexity', 'unknown')}
- Key Requirements: {', '.join(context.get('key_requirements', []))}

"""

        # Add relevant context from Knowledge Base
        if kb_context:
            prompt += f"""Relevant Context from Previous Work:
{kb_context}

"""

        prompt += """Please complete this task following your expertise and output format.
Provide specific, actionable deliverables in JSON format."""

        return prompt

    async def _fetch_relevant_context(self, task: Task) -> str:
        """
        Fetch relevant context from Knowledge Base for this task.

        Args:
            task: Task object

        Returns:
            Formatted context string
        """
        try:
            # Build query from task title and description
            query = f"{task.title}. {task.description}"

            # Fetch context using knowledge service
            async with get_db() as db:
                context = await knowledge_service.get_context_for_agent(
                    agent_type=self.agent_type,
                    query=query,
                    top_k=3,  # Get top 3 most relevant entries
                    db=db,
                )

            if context:
                logger.debug(f"Fetched KB context for task {task.id} ({len(context)} chars)")
            else:
                logger.debug(f"No relevant KB context found for task {task.id}")

            return context

        except Exception as e:
            # Log error but don't fail the task
            logger.warning(f"Failed to fetch KB context for task {task.id}: {e}")
            return ""


class AgentRegistry:
    """
    Registry of all available agents
    Manages agent instances and assignment
    """

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._register_agents()

    @property
    def agents(self) -> Dict[str, BaseAgent]:
        """Get all registered agents."""
        return self._agents

    def _register_agents(self):
        """Register all available agents"""
        # Import agents here to avoid circular imports
        from app.agents.marketing_agent import MarketingAgent
        from app.agents.frontend_agent import FrontendDeveloperAgent
        from app.agents.backend_agent import BackendDeveloperAgent
        from app.agents.data_analyst_agent import DataAnalystAgent
        from app.agents.ux_designer_agent import UXDesignerAgent
        from app.agents.content_writer_agent import ContentWriterAgent
        from app.agents.mobile_developer_agent import MobileDeveloperAgent
        from app.agents.devops_engineer_agent import DevOpsEngineerAgent
        from app.agents.project_manager_agent import ProjectManagerAgent
        from app.agents.qa_engineer_agent import QAEngineerAgent
        from app.agents.hr_agent import HRAgent

        # Register agents
        self.register(MarketingAgent())
        self.register(FrontendDeveloperAgent())
        self.register(BackendDeveloperAgent())
        self.register(DataAnalystAgent())
        self.register(UXDesignerAgent())
        self.register(ContentWriterAgent())
        self.register(MobileDeveloperAgent())
        self.register(DevOpsEngineerAgent())
        self.register(ProjectManagerAgent())
        self.register(QAEngineerAgent())
        self.register(HRAgent())

        logger.info(f"Registered {len(self._agents)} agents")

    def register(self, agent: BaseAgent):
        """Register an agent"""
        self._agents[agent.agent_type] = agent
        logger.debug(f"Registered agent: {agent.agent_type}")

    def get_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Get agent by type"""
        return self._agents.get(agent_type)

    def list_agents(self) -> list:
        """List all registered agents"""
        return list(self._agents.keys())

    async def execute_task(self, agent_type: str, task: Task) -> Dict[str, Any]:
        """
        Execute task with specified agent

        Args:
            agent_type: Type of agent to use
            task: Task to execute

        Returns:
            Execution result
        """
        agent = self.get_agent(agent_type)

        if not agent:
            raise ValueError(f"Agent type '{agent_type}' not found")

        return await agent.execute_task(task)


# Global instance
agent_registry = AgentRegistry()
