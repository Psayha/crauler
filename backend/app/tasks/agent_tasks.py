"""
Celery Tasks for Agent Operations

Background tasks for agent execution and management.
"""

import logging
import asyncio
from uuid import UUID

from app.celery_app import celery_app
from app.database.connection import get_db
from app.services.executor import task_executor

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.agent_tasks.execute_task_async", bind=True, max_retries=3)
def execute_task_async(self, task_id: str):
    """
    Execute single task asynchronously via Celery.

    Args:
        task_id: Task UUID string

    Returns:
        Task execution result
    """
    logger.info(f"Starting async execution of task {task_id}")

    try:
        task_uuid = UUID(task_id)

        result = asyncio.run(_execute_task_internal(task_uuid))

        logger.info(f"Task {task_id} execution completed via Celery")

        return result

    except Exception as e:
        logger.error(f"Error executing task {task_id}: {e}", exc_info=True)

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=30 * (2 ** self.request.retries))


async def _execute_task_internal(task_id: UUID):
    """Internal async function to execute task."""
    async with get_db() as db:
        result = await task_executor.execute_task(task_id, db)
    return result


@celery_app.task(name="app.tasks.agent_tasks.execute_task_batch_async")
def execute_task_batch_async(task_ids: list[str], parallel: bool = True):
    """
    Execute multiple tasks asynchronously.

    Args:
        task_ids: List of task UUID strings
        parallel: Execute in parallel if True

    Returns:
        List of execution results
    """
    logger.info(f"Starting batch execution of {len(task_ids)} tasks (parallel={parallel})")

    try:
        task_uuids = [UUID(tid) for tid in task_ids]

        results = asyncio.run(_execute_batch_internal(task_uuids, parallel))

        logger.info(f"Batch execution completed: {len(results)} tasks")

        return results

    except Exception as e:
        logger.error(f"Error executing task batch: {e}", exc_info=True)
        return {"error": str(e)}


async def _execute_batch_internal(task_ids: list[UUID], parallel: bool):
    """Internal async function to execute task batch."""
    async with get_db() as db:
        results = await task_executor.execute_task_batch(task_ids, db, parallel)
    return results
