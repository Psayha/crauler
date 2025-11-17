"""
Orchestrator Service

Manages project execution, task decomposition, parallel execution,
progress tracking, and result aggregation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskStatus
from app.services.executor import task_executor, TaskExecutor
from app.services.knowledge_service import knowledge_service
from app.database.connection import get_db
from app.websockets.manager import ws_manager

logger = logging.getLogger(__name__)


class OrchestratorService:
    """
    Orchestrates project execution with intelligent task management.

    Features:
    - Smart task decomposition
    - Dependency resolution and ordering
    - Parallel execution of independent tasks
    - Real-time progress tracking
    - Result aggregation
    """

    def __init__(self, executor: TaskExecutor = None):
        """
        Initialize OrchestratorService.

        Args:
            executor: TaskExecutor instance (uses global if not provided)
        """
        self.executor = executor or task_executor
        logger.info("OrchestratorService initialized")

    async def execute_project(
        self,
        project_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Execute entire project.

        Orchestrates execution of all tasks with dependency management
        and parallel execution where possible.

        Args:
            project_id: Project UUID
            db: Database session

        Returns:
            Project execution results
        """
        logger.info(f"Starting execution of project {project_id}")

        # Get project
        project = await self._get_project(project_id, db)

        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Check project status
        if project.status not in [ProjectStatus.PLANNING, ProjectStatus.READY]:
            raise ValueError(
                f"Project must be in PLANNING or READY status, currently: {project.status.value}"
            )

        try:
            # Update project status to IN_PROGRESS
            await self._update_project_status(project, ProjectStatus.IN_PROGRESS, db)

            # Send WebSocket notification
            await self._notify_project_status(project, "started")

            # Get all tasks for project
            tasks = await self._get_project_tasks(project_id, db)

            if not tasks:
                logger.warning(f"No tasks found for project {project_id}")
                await self._complete_project(project, {}, db)
                return {"status": "completed", "message": "No tasks to execute"}

            logger.info(f"Found {len(tasks)} tasks for project {project_id}")

            # Build dependency graph
            task_graph = self._build_task_graph(tasks)

            # Calculate execution order with parallelization
            execution_plan = self._create_execution_plan(task_graph, tasks)

            logger.info(f"Execution plan created: {len(execution_plan)} waves")

            # Execute tasks wave by wave
            results = await self._execute_waves(execution_plan, db, project)

            # Aggregate results
            aggregated_results = self._aggregate_results(results, tasks)

            # Update project status
            if aggregated_results["failed_count"] > 0:
                await self._fail_project(
                    project,
                    f"Project completed with {aggregated_results['failed_count']} failed tasks",
                    db
                )
                await self._notify_project_status(project, "failed", aggregated_results)
            else:
                await self._complete_project(project, aggregated_results, db)
                await self._notify_project_status(project, "completed", aggregated_results)

            logger.info(f"Project {project_id} execution completed")

            return {
                "status": "success",
                "project_id": str(project_id),
                "total_tasks": aggregated_results["total_tasks"],
                "completed_tasks": aggregated_results["completed_tasks"],
                "failed_tasks": aggregated_results["failed_count"],
                "execution_time_seconds": aggregated_results.get("execution_time_seconds", 0),
                "results": aggregated_results
            }

        except Exception as e:
            logger.error(f"Error executing project {project_id}: {e}", exc_info=True)
            await self._fail_project(project, str(e), db)
            await self._notify_project_status(project, "failed", {"error": str(e)})
            raise

    async def get_project_status(
        self,
        project_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get current project status.

        Args:
            project_id: Project UUID
            db: Database session

        Returns:
            Project status information
        """
        project = await self._get_project(project_id, db)

        if not project:
            raise ValueError(f"Project {project_id} not found")

        tasks = await self._get_project_tasks(project_id, db)

        task_statuses = {}
        for status in TaskStatus:
            task_statuses[status.value] = sum(
                1 for t in tasks if t.status == status
            )

        return {
            "project_id": str(project_id),
            "name": project.name,
            "status": project.status.value,
            "total_tasks": len(tasks),
            "task_statuses": task_statuses,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "started_at": project.started_at.isoformat() if hasattr(project, 'started_at') and project.started_at else None,
            "completed_at": project.completed_at.isoformat() if hasattr(project, 'completed_at') and project.completed_at else None,
        }

    async def get_project_progress(
        self,
        project_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get detailed project progress.

        Args:
            project_id: Project UUID
            db: Database session

        Returns:
            Detailed progress information
        """
        project = await self._get_project(project_id, db)

        if not project:
            raise ValueError(f"Project {project_id} not found")

        tasks = await self._get_project_tasks(project_id, db)

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)

        progress_percentage = (completed / total * 100) if total > 0 else 0

        # Calculate estimated tokens
        total_estimated_tokens = sum(t.estimated_tokens for t in tasks)
        total_actual_tokens = sum(t.actual_tokens for t in tasks)

        # Group tasks by agent
        tasks_by_agent = {}
        for task in tasks:
            agent = task.assigned_agent
            if agent not in tasks_by_agent:
                tasks_by_agent[agent] = []
            tasks_by_agent[agent].append({
                "id": str(task.id),
                "title": task.title,
                "status": task.status.value
            })

        return {
            "project_id": str(project_id),
            "name": project.name,
            "status": project.status.value,
            "progress_percentage": round(progress_percentage, 2),
            "total_tasks": total,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "failed_tasks": failed,
            "pending_tasks": pending,
            "total_estimated_tokens": total_estimated_tokens,
            "total_actual_tokens": total_actual_tokens,
            "tasks_by_agent": tasks_by_agent,
        }

    def _build_task_graph(self, tasks: List[Task]) -> Dict[UUID, Set[UUID]]:
        """
        Build dependency graph for tasks.

        Args:
            tasks: List of tasks

        Returns:
            Dictionary mapping task_id -> set of dependency task_ids
        """
        graph = {}
        for task in tasks:
            graph[task.id] = set(task.dependencies) if task.dependencies else set()

        logger.debug(f"Built task graph with {len(graph)} nodes")
        return graph

    def _create_execution_plan(
        self,
        task_graph: Dict[UUID, Set[UUID]],
        tasks: List[Task]
    ) -> List[List[UUID]]:
        """
        Create execution plan with waves of parallel tasks.

        Uses topological sort to create waves of tasks that can be
        executed in parallel.

        Args:
            task_graph: Dependency graph
            tasks: List of tasks

        Returns:
            List of task waves (each wave can be executed in parallel)
        """
        # Create task map for quick lookup
        task_map = {t.id: t for t in tasks}

        # Calculate in-degree for each task
        in_degree = {task_id: len(deps) for task_id, deps in task_graph.items()}

        # Find tasks with no dependencies (wave 0)
        waves = []
        remaining_tasks = set(task_graph.keys())

        while remaining_tasks:
            # Find tasks ready to execute (in-degree == 0)
            current_wave = [
                task_id for task_id in remaining_tasks
                if in_degree[task_id] == 0
            ]

            if not current_wave:
                # Circular dependency detected
                logger.error(f"Circular dependency detected in remaining tasks: {remaining_tasks}")
                # Add remaining tasks to final wave (will fail dependency check)
                waves.append(list(remaining_tasks))
                break

            waves.append(current_wave)

            # Remove current wave from remaining
            for task_id in current_wave:
                remaining_tasks.remove(task_id)

                # Reduce in-degree of dependent tasks
                for other_task_id in remaining_tasks:
                    if task_id in task_graph[other_task_id]:
                        in_degree[other_task_id] -= 1

        logger.info(f"Created execution plan with {len(waves)} waves")
        for i, wave in enumerate(waves):
            logger.debug(f"Wave {i}: {len(wave)} tasks")

        return waves

    async def _execute_waves(
        self,
        waves: List[List[UUID]],
        db: AsyncSession,
        project: Project
    ) -> List[Dict[str, Any]]:
        """
        Execute task waves sequentially, tasks within wave in parallel.

        Args:
            waves: List of task waves
            db: Database session
            project: Project instance

        Returns:
            List of execution results
        """
        all_results = []
        start_time = datetime.utcnow()

        for wave_index, wave in enumerate(waves):
            logger.info(f"Executing wave {wave_index + 1}/{len(waves)} with {len(wave)} tasks")

            # Send progress update
            await self._notify_progress(
                project,
                wave_index + 1,
                len(waves),
                len(all_results),
                sum(len(w) for w in waves)
            )

            # Execute tasks in parallel within wave
            wave_results = await self.executor.execute_task_batch(
                task_ids=wave,
                db=db,
                parallel=True
            )

            all_results.extend(wave_results)

            # Check for failures
            failed_in_wave = [
                r for r in wave_results
                if isinstance(r, Exception) or r.get("status") == "error"
            ]

            if failed_in_wave:
                logger.warning(
                    f"Wave {wave_index + 1} completed with {len(failed_in_wave)} failures"
                )

        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()

        logger.info(
            f"All waves executed in {execution_time:.2f}s, "
            f"{len(all_results)} total tasks"
        )

        return all_results

    def _aggregate_results(
        self,
        results: List[Any],
        tasks: List[Task]
    ) -> Dict[str, Any]:
        """
        Aggregate execution results.

        Args:
            results: List of task execution results
            tasks: List of tasks

        Returns:
            Aggregated results
        """
        successful_results = [
            r for r in results
            if not isinstance(r, Exception) and r.get("status") == "success"
        ]

        failed_results = [
            r for r in results
            if isinstance(r, Exception) or r.get("status") == "error"
        ]

        total_tokens = sum(
            r.get("tokens_used", 0) for r in successful_results
        )

        # Group by agent
        results_by_agent = {}
        for result in successful_results:
            agent = result.get("agent")
            if agent:
                if agent not in results_by_agent:
                    results_by_agent[agent] = []
                results_by_agent[agent].append(result)

        return {
            "total_tasks": len(results),
            "completed_tasks": len(successful_results),
            "failed_count": len(failed_results),
            "success_rate": len(successful_results) / len(results) * 100 if results else 0,
            "total_tokens_used": total_tokens,
            "results_by_agent": {
                agent: len(results) for agent, results in results_by_agent.items()
            },
            "failed_tasks": [
                {
                    "task_id": str(r.get("task_id", "unknown")),
                    "error": str(r.get("error", r)) if isinstance(r, Exception) else r.get("error", "Unknown error")
                }
                for r in failed_results
            ]
        }

    async def _get_project(self, project_id: UUID, db: AsyncSession) -> Optional[Project]:
        """Get project from database."""
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def _get_project_tasks(self, project_id: UUID, db: AsyncSession) -> List[Task]:
        """Get all tasks for project."""
        result = await db.execute(
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.created_at)
        )
        return list(result.scalars().all())

    async def _update_project_status(
        self,
        project: Project,
        status: ProjectStatus,
        db: AsyncSession
    ):
        """Update project status."""
        project.status = status
        project.updated_at = datetime.utcnow()

        if status == ProjectStatus.IN_PROGRESS and not hasattr(project, 'started_at'):
            project.started_at = datetime.utcnow()

        await db.commit()
        await db.refresh(project)

        logger.debug(f"Project {project.id} status updated to {status.value}")

    async def _complete_project(
        self,
        project: Project,
        results: Dict[str, Any],
        db: AsyncSession
    ):
        """Mark project as completed."""
        project.status = ProjectStatus.COMPLETED
        project.completed_at = datetime.utcnow()

        # Store results in metadata
        if not project.project_metadata:
            project.project_metadata = {}

        project.project_metadata["execution_results"] = results

        await db.commit()

        # Store project results in Knowledge Base
        try:
            await self._store_project_in_kb(project, results, db)
        except Exception as kb_error:
            # Log error but don't fail the project
            logger.warning(f"Failed to store project {project.id} in Knowledge Base: {kb_error}")
        await db.refresh(project)

        logger.info(f"Project {project.id} completed successfully")

    async def _fail_project(
        self,
        project: Project,
        error_message: str,
        db: AsyncSession
    ):
        """Mark project as failed."""
        project.status = ProjectStatus.FAILED

        if not project.project_metadata:
            project.project_metadata = {}

        project.project_metadata["error"] = error_message

        await db.commit()
        await db.refresh(project)

        logger.error(f"Project {project.id} failed: {error_message}")

    async def _notify_project_status(
        self,
        project: Project,
        status: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Send WebSocket notification about project status."""
        try:
            message = {
                "type": "project_update",
                "project_id": str(project.id),
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if data:
                message["data"] = data

            await ws_manager.broadcast_to_project(
                project_id=str(project.id),
                message=message
            )

            logger.debug(f"Sent project notification: {status}")

        except Exception as e:
            logger.warning(f"Failed to send project notification: {e}")

    async def _notify_progress(
        self,
        project: Project,
        current_wave: int,
        total_waves: int,
        completed_tasks: int,
        total_tasks: int
    ):
        """Send progress update via WebSocket."""
        try:
            progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            message = {
                "type": "project_progress",
                "project_id": str(project.id),
                "current_wave": current_wave,
                "total_waves": total_waves,
                "completed_tasks": completed_tasks,
                "total_tasks": total_tasks,
                "progress_percentage": round(progress_percentage, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }

            await ws_manager.broadcast_to_project(
                project_id=str(project.id),
                message=message
            )

        except Exception as e:
            logger.warning(f"Failed to send progress update: {e}")

    async def _store_project_in_kb(
        self,
        project: Project,
        results: Dict[str, Any],
        db: AsyncSession
    ):
        """
        Store project results in Knowledge Base.

        Args:
            project: Completed project
            results: Project execution results
            db: Database session
        """
        try:
            # Aggregate task outputs
            task_summaries = []
            for agent_name, agent_results in results.get("by_agent", {}).items():
                for task_result in agent_results.get("tasks", []):
                    if task_result.get("status") == "success":
                        task_summaries.append(
                            f"- {task_result.get('title', 'Untitled')}: "
                            f"{task_result.get('output', 'No output')[:200]}"
                        )

            # Create content
            title = f"Project: {project.name}"
            content = f"""
Project: {project.name}
Type: {project.type.value}
Description: {project.description or 'N/A'}
Status: {project.status.value}
Priority: {project.priority}

Execution Summary:
- Total Tasks: {results.get('total_tasks', 0)}
- Completed: {results.get('completed_tasks', 0)}
- Failed: {results.get('failed_tasks', 0)}
- Total Tokens: {results.get('total_tokens', 0)}

Task Results:
{chr(10).join(task_summaries[:20]) if task_summaries else 'No task outputs'}

Completion Time: {project.completed_at.isoformat() if project.completed_at else 'N/A'}
""".strip()

            # Prepare metadata
            metadata = {
                "project_id": str(project.id),
                "project_type": project.type.value,
                "priority": project.priority,
                "total_tasks": results.get("total_tasks", 0),
                "completed_tasks": results.get("completed_tasks", 0),
                "failed_tasks": results.get("failed_tasks", 0),
                "total_tokens": results.get("total_tokens", 0),
                "agents_used": list(results.get("by_agent", {}).keys()),
                "started_at": project.started_at.isoformat() if project.started_at else None,
                "completed_at": project.completed_at.isoformat() if project.completed_at else None,
            }

            # Extract tags
            tags = [
                project.type.value,
                project.priority,
                "project_output",
                "completed",
            ]

            # Add agent types as tags
            tags.extend(results.get("by_agent", {}).keys())

            # Store in Knowledge Base
            await knowledge_service.store_knowledge(
                title=title,
                content=content,
                content_type="project_output",
                source_type="project",
                source_id=project.id,
                agent_type="orchestrator",
                tags=tags,
                metadata=metadata,
                db=db,
            )

            logger.info(f"Stored project {project.id} results in Knowledge Base")

        except Exception as e:
            logger.error(f"Failed to store project {project.id} in KB: {e}", exc_info=True)
            raise


# Global instance
orchestrator_service = OrchestratorService()
