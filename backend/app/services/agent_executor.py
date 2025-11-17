import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.task import Task, TaskStatus
from app.models.project import Project, ProjectStatus
from app.agents.base_agent import agent_registry
from app.database.connection import get_db

logger = logging.getLogger(__name__)


class AgentExecutor:
    """
    Service for executing tasks with AI agents
    Manages task execution flow, dependencies, and state
    """

    def __init__(self):
        self.agent_registry = agent_registry

    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a single task with appropriate agent

        Args:
            task_id: Task ID to execute

        Returns:
            Execution result
        """
        async with get_db() as db:
            # Get task
            result = await db.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                raise ValueError(f"Task {task_id} not found")

            if task.status != TaskStatus.PENDING:
                raise ValueError(
                    f"Task {task_id} is not pending, status: {task.status.value}"
                )

            # Check if agent is available
            agent = self.agent_registry.get_agent(task.assigned_agent)
            if not agent:
                raise ValueError(
                    f"Agent '{task.assigned_agent}' not found for task {task_id}"
                )

            # Update task status to in_progress
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.utcnow()
            await db.commit()

            logger.info(
                f"Starting task {task_id}: {task.title} with {task.assigned_agent}"
            )

        try:
            # Execute task with agent
            result = await self.agent_registry.execute_task(
                task.assigned_agent, task
            )

            # Update task status based on result
            async with get_db() as db:
                result_db = await db.execute(
                    select(Task).where(Task.id == task_id)
                )
                task = result_db.scalar_one()

                if result["status"] == "success":
                    task.status = TaskStatus.COMPLETED
                    logger.info(f"Task {task_id} completed successfully")
                else:
                    task.status = TaskStatus.FAILED
                    logger.error(f"Task {task_id} failed: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {e}")

            # Update task status to failed
            async with get_db() as db:
                result_db = await db.execute(
                    select(Task).where(Task.id == task_id)
                )
                task = result_db.scalar_one()
                task.status = TaskStatus.FAILED

            raise

    async def execute_project(self, project_id: str) -> Dict[str, Any]:
        """
        Execute all tasks for a project

        Args:
            project_id: Project ID to execute

        Returns:
            Execution summary
        """
        async with get_db() as db:
            # Get project with tasks
            result = await db.execute(
                select(Project)
                .options(selectinload(Project.tasks))
                .where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                raise ValueError(f"Project {project_id} not found")

            if project.status != ProjectStatus.IN_PROGRESS:
                raise ValueError(
                    f"Project must be IN_PROGRESS, currently: {project.status.value}"
                )

            tasks = project.tasks

        logger.info(f"Executing project {project_id} with {len(tasks)} tasks")

        # Execute tasks respecting dependencies
        completed_tasks = []
        failed_tasks = []

        # Group tasks by dependency level
        task_levels = self._build_task_levels(tasks)

        for level, level_tasks in enumerate(task_levels):
            logger.info(f"Executing level {level} with {len(level_tasks)} tasks")

            # Execute tasks in this level in parallel
            level_results = await asyncio.gather(
                *[
                    self.execute_task(str(task.id))
                    for task in level_tasks
                    if task.status == TaskStatus.PENDING
                ],
                return_exceptions=True,
            )

            # Process results
            for i, result in enumerate(level_results):
                task = level_tasks[i]

                if isinstance(result, Exception):
                    logger.error(f"Task {task.id} failed: {result}")
                    failed_tasks.append(task)
                elif result.get("status") == "success":
                    completed_tasks.append(task)
                else:
                    failed_tasks.append(task)

            # Stop if any task in this level failed
            if failed_tasks:
                logger.warning(
                    f"Level {level} had failures, stopping execution"
                )
                break

        # Update project status
        async with get_db() as db:
            result = await db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one()

            if failed_tasks:
                project.status = ProjectStatus.REVIEW
                logger.info(f"Project {project_id} needs review due to failures")
            else:
                project.status = ProjectStatus.COMPLETED
                logger.info(f"Project {project_id} completed successfully")

        return {
            "project_id": str(project_id),
            "status": project.status.value,
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "completed_task_ids": [str(t.id) for t in completed_tasks],
            "failed_task_ids": [str(t.id) for t in failed_tasks],
        }

    def _build_task_levels(self, tasks: List[Task]) -> List[List[Task]]:
        """
        Build task execution levels based on dependencies

        Tasks with no dependencies are level 0
        Tasks depending only on level 0 are level 1, etc.

        Args:
            tasks: List of tasks

        Returns:
            List of task levels, where each level is a list of tasks
        """
        task_map = {str(task.id): task for task in tasks}
        levels = []
        remaining = set(task_map.keys())
        completed_ids = set()

        while remaining:
            # Find tasks with all dependencies completed
            current_level = []

            for task_id in list(remaining):
                task = task_map[task_id]
                dependencies = task.dependencies or []

                # Check if all dependencies are completed
                if all(str(dep_id) in completed_ids for dep_id in dependencies):
                    current_level.append(task)
                    remaining.remove(task_id)
                    completed_ids.add(task_id)

            if not current_level:
                # Circular dependency or missing dependency
                logger.warning(
                    f"Could not resolve dependencies for tasks: {remaining}"
                )
                # Add remaining tasks to current level to avoid infinite loop
                current_level = [task_map[task_id] for task_id in remaining]
                remaining.clear()

            levels.append(current_level)

        return levels

    async def retry_task(self, task_id: str) -> Dict[str, Any]:
        """
        Retry a failed task

        Args:
            task_id: Task ID to retry

        Returns:
            Execution result
        """
        async with get_db() as db:
            result = await db.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                raise ValueError(f"Task {task_id} not found")

            if task.status != TaskStatus.FAILED:
                raise ValueError(
                    f"Can only retry failed tasks, current status: {task.status.value}"
                )

            # Reset task status
            task.status = TaskStatus.PENDING
            task.started_at = None
            task.completed_at = None

            logger.info(f"Retrying task {task_id}: {task.title}")

        return await self.execute_task(task_id)


# Global instance
agent_executor = AgentExecutor()
