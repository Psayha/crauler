"""
Task Executor Service

Handles execution of tasks by AI agents with dependency resolution,
retry mechanism, error handling, and rollback capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.models.agent_execution import AgentExecution
from app.models.project import Project, ProjectStatus
from app.agents.registry import get_agent
from app.database.connection import get_db
from app.websockets.manager import ws_manager
from app.services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)


class TaskExecutionError(Exception):
    """Custom exception for task execution errors."""
    pass


class DependencyError(Exception):
    """Exception raised when task dependencies are not met."""
    pass


class TaskExecutor:
    """
    Executes tasks using AI agents with full lifecycle management.

    Features:
    - Dependency resolution
    - Retry mechanism with exponential backoff
    - Error handling and rollback
    - Progress tracking
    - Real-time WebSocket notifications
    """

    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        """
        Initialize TaskExecutor.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        logger.info(f"TaskExecutor initialized (max_retries={max_retries}, retry_delay={retry_delay}s)")

    async def execute_task(
        self,
        task_id: UUID,
        db: AsyncSession,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Execute a single task.

        Args:
            task_id: Task UUID
            db: Database session
            retry_count: Current retry attempt number

        Returns:
            Task execution result

        Raises:
            TaskExecutionError: If execution fails after all retries
            DependencyError: If task dependencies are not met
        """
        logger.info(f"Starting execution of task {task_id} (attempt {retry_count + 1}/{self.max_retries + 1})")

        # Get task from database
        task = await self._get_task(task_id, db)

        if not task:
            raise TaskExecutionError(f"Task {task_id} not found")

        # Check if task is already completed
        if task.status == TaskStatus.COMPLETED:
            logger.info(f"Task {task_id} already completed, skipping")
            return {"status": "already_completed", "task_id": str(task_id)}

        try:
            # Check dependencies
            await self._check_dependencies(task, db)

            # Update task status to IN_PROGRESS
            await self._update_task_status(task, TaskStatus.IN_PROGRESS, db)

            # Send WebSocket notification
            await self._notify_task_status(task, "in_progress")

            # Get agent for this task
            agent = get_agent(task.assigned_agent)

            if not agent:
                raise TaskExecutionError(f"Agent {task.assigned_agent} not found")

            # Create agent execution record
            execution = await self._create_execution_record(task, db)

            # Execute task with agent
            logger.info(f"Executing task {task_id} with agent {task.assigned_agent}")

            result = await agent.execute_task(task)

            # Check if execution failed
            if result.get("status") == "failed":
                # Update execution record with failure
                await self._update_execution_record(
                    execution=execution,
                    result=result,
                    db=db
                )
                # Raise exception to trigger retry logic
                raise TaskExecutionError(result.get("error", "Unknown error"))

            # Update execution record with results
            await self._update_execution_record(
                execution=execution,
                result=result,
                db=db
            )

            # Update task with results
            await self._complete_task(task, result, db)

            # Store result in Knowledge Base
            try:
                await self._store_in_knowledge_base(task, result, db)
            except Exception as kb_error:
                # Log error but don't fail the task
                logger.warning(f"Failed to store task {task_id} in Knowledge Base: {kb_error}")

            # Send success notification
            await self._notify_task_status(task, "completed", result)

            logger.info(f"Task {task_id} completed successfully")

            return {
                "status": "success",
                "task_id": str(task_id),
                "agent": task.assigned_agent,
                "result": result,
                "tokens_used": execution.tokens_used
            }

        except DependencyError as e:
            logger.error(f"Dependency error for task {task_id}: {e}")
            await self._fail_task(task, str(e), db)
            await self._notify_task_status(task, "failed", {"error": str(e)})
            raise

        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}", exc_info=True)

            # Retry logic
            if retry_count < self.max_retries:
                delay = self.retry_delay * (2 ** retry_count)  # Exponential backoff
                logger.info(f"Retrying task {task_id} in {delay}s (attempt {retry_count + 2}/{self.max_retries + 1})")

                await asyncio.sleep(delay)
                return await self.execute_task(task_id, db, retry_count + 1)

            # Max retries reached, fail task
            await self._fail_task(task, str(e), db)
            await self._notify_task_status(task, "failed", {"error": str(e)})

            raise TaskExecutionError(f"Task {task_id} failed after {self.max_retries + 1} attempts: {e}")

    async def execute_task_batch(
        self,
        task_ids: List[UUID],
        db: AsyncSession,
        parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tasks.

        Args:
            task_ids: List of task UUIDs
            db: Database session (ignored in parallel mode - each task gets its own session)
            parallel: Execute tasks in parallel if True

        Returns:
            List of task execution results
        """
        logger.info(f"Executing batch of {len(task_ids)} tasks (parallel={parallel})")

        if parallel:
            # Execute tasks in parallel - each with its own DB session
            async def execute_with_new_session(task_id: UUID):
                from app.database.connection import get_db
                async with get_db() as task_db:
                    return await self.execute_task(task_id, task_db)

            raw_results = await asyncio.gather(
                *[execute_with_new_session(task_id) for task_id in task_ids],
                return_exceptions=True
            )
            # Convert exceptions to error dicts
            results = []
            for i, result in enumerate(raw_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to execute task {task_ids[i]}: {result}")
                    results.append({"status": "error", "task_id": str(task_ids[i]), "error": str(result)})
                else:
                    results.append(result)
        else:
            # Execute tasks sequentially
            results = []
            for task_id in task_ids:
                try:
                    result = await self.execute_task(task_id, db)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to execute task {task_id}: {e}")
                    results.append({"status": "error", "task_id": str(task_id), "error": str(e)})

        return results

    async def _get_task(self, task_id: UUID, db: AsyncSession) -> Optional[Task]:
        """Get task from database."""
        result = await db.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def _check_dependencies(self, task: Task, db: AsyncSession):
        """
        Check if all task dependencies are completed.

        Args:
            task: Task to check
            db: Database session

        Raises:
            DependencyError: If dependencies are not met
        """
        if not task.dependencies:
            return

        logger.debug(f"Checking dependencies for task {task.id}: {task.dependencies}")

        # Get dependency tasks
        result = await db.execute(
            select(Task).where(Task.id.in_(task.dependencies))
        )
        dependency_tasks = result.scalars().all()

        # Check if all dependencies are completed
        incomplete_deps = [
            str(t.id) for t in dependency_tasks
            if t.status != TaskStatus.COMPLETED
        ]

        if incomplete_deps:
            raise DependencyError(
                f"Task {task.id} has incomplete dependencies: {incomplete_deps}"
            )

        logger.debug(f"All dependencies met for task {task.id}")

    async def _update_task_status(
        self,
        task: Task,
        status: TaskStatus,
        db: AsyncSession
    ):
        """Update task status in database."""
        task.status = status
        task.updated_at = datetime.utcnow()

        if status == TaskStatus.IN_PROGRESS:
            task.started_at = datetime.utcnow()
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(task)

        logger.debug(f"Task {task.id} status updated to {status.value}")

    async def _create_execution_record(
        self,
        task: Task,
        db: AsyncSession
    ) -> AgentExecution:
        """Create agent execution record."""
        execution = AgentExecution(
            id=uuid4(),
            task_id=task.id,
            agent_type=task.assigned_agent,
            status="in_progress"
        )

        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        logger.debug(f"Created execution record {execution.id} for task {task.id}")

        return execution

    async def _update_execution_record(
        self,
        execution: AgentExecution,
        result: Dict[str, Any],
        db: AsyncSession
    ):
        """Update execution record with results."""
        if result.get("status") == "failed":
            execution.status = "failed"
            execution.error_message = result.get("error", "Unknown error")
            execution.prompt = result.get("prompt", "")
            execution.execution_time_ms = result.get("execution_time_ms", 0)
        else:
            execution.status = "completed"
            execution.prompt = result.get("prompt", "")
            execution.response = result.get("response", "")
            execution.tokens_used = result.get("tokens_used", 0)
            execution.execution_time_ms = result.get("execution_time_ms", 0)
            execution.execution_metadata = result.get("metadata", {})

        await db.commit()
        await db.refresh(execution)

        logger.debug(f"Updated execution record {execution.id} with status {execution.status}")

    async def _complete_task(
        self,
        task: Task,
        result: Dict[str, Any],
        db: AsyncSession
    ):
        """Mark task as completed with results."""
        task.status = TaskStatus.COMPLETED
        task.output_data = result.get("result", result)
        task.completed_at = datetime.utcnow()
        task.actual_tokens = result.get("tokens_used", 0)

        await db.commit()
        await db.refresh(task)

        logger.info(f"Task {task.id} marked as completed")

    async def _fail_task(
        self,
        task: Task,
        error_message: str,
        db: AsyncSession
    ):
        """Mark task as failed."""
        task.status = TaskStatus.FAILED
        task.output_data = {"error": error_message}
        task.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(task)

        logger.error(f"Task {task.id} marked as failed: {error_message}")

    async def _notify_task_status(
        self,
        task: Task,
        status: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Send WebSocket notification about task status."""
        try:
            message = {
                "type": "task_update",
                "task_id": str(task.id),
                "project_id": str(task.project_id),
                "status": status,
                "agent": task.assigned_agent,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if data:
                message["data"] = data

            await ws_manager.broadcast_to_project(
                project_id=str(task.project_id),
                message=message
            )

            logger.debug(f"Sent WebSocket notification for task {task.id}: {status}")

        except Exception as e:
            logger.warning(f"Failed to send WebSocket notification: {e}")

    async def rollback_task(self, task_id: UUID, db: AsyncSession):
        """
        Rollback task execution.

        Resets task status to PENDING and clears execution data.

        Args:
            task_id: Task UUID
            db: Database session
        """
        logger.info(f"Rolling back task {task_id}")

        task = await self._get_task(task_id, db)

        if not task:
            raise TaskExecutionError(f"Task {task_id} not found")

        # Reset task status
        task.status = TaskStatus.PENDING
        task.output_data = {}
        task.started_at = None
        task.completed_at = None
        task.actual_tokens = 0
        task.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(task)

        logger.info(f"Task {task_id} rolled back successfully")

    async def _store_in_knowledge_base(
        self,
        task: Task,
        result: Dict[str, Any],
        db: AsyncSession
    ):
        """
        Store task result in Knowledge Base for future reference.

        Args:
            task: Completed task
            result: Task execution result
            db: Database session
        """
        try:
            # Extract output text from result
            output_text = result.get("output", "")

            # If output is a dict, convert to string
            if isinstance(output_text, dict):
                output_text = str(output_text)

            # Only store if we have meaningful content
            if not output_text or len(output_text) < 10:
                logger.debug(f"Skipping KB storage for task {task.id} - no meaningful output")
                return

            # Prepare content
            title = f"Task Result: {task.title}"
            content = f"""
Task: {task.title}
Description: {task.description or 'N/A'}
Agent: {task.assigned_agent}
Status: {task.status.value}

Output:
{output_text}
""".strip()

            # Prepare metadata
            metadata = {
                "task_id": str(task.id),
                "project_id": str(task.project_id),
                "agent": task.assigned_agent,
                "priority": task.priority.value,
                "tokens_used": result.get("tokens_used", 0),
                "execution_time_ms": result.get("execution_time_ms"),
                "success": result.get("status") == "success",
            }

            # Store in Knowledge Base
            await knowledge_service.store_knowledge(
                title=title,
                content=content,
                content_type="task_result",
                source_type="task",
                source_id=task.id,
                agent_type=task.assigned_agent,
                tags=[task.assigned_agent, task.priority.value, "task_result"],
                metadata=metadata,
                db=db,
            )

            logger.info(f"Stored task {task.id} result in Knowledge Base")

        except Exception as e:
            # Log but don't fail - KB storage is not critical
            logger.error(f"Failed to store task {task.id} in KB: {e}", exc_info=True)
            raise


# Global instance
task_executor = TaskExecutor()
