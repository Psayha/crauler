"""
Celery Tasks for Project Operations

Background tasks for project execution and management.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import select

from app.celery_app import celery_app
from app.database.connection import get_db
from app.models.project import Project, ProjectStatus
from app.services.orchestrator_service import orchestrator_service

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.project_tasks.execute_project_async", bind=True, max_retries=2)
def execute_project_async(self, project_id: str):
    """
    Execute project asynchronously via Celery.

    Args:
        project_id: Project UUID string

    Returns:
        Execution results
    """
    logger.info(f"Starting async execution of project {project_id}")

    try:
        # Convert to UUID
        project_uuid = UUID(project_id)

        # Run async orchestrator service
        result = asyncio.run(_execute_project_internal(project_uuid))

        logger.info(f"Project {project_id} execution completed via Celery")

        return result

    except Exception as e:
        logger.error(f"Error executing project {project_id}: {e}", exc_info=True)

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


async def _execute_project_internal(project_id: UUID):
    """Internal async function to execute project."""
    async with get_db() as db:
        result = await orchestrator_service.execute_project(project_id, db)
    return result


@celery_app.task(name="app.tasks.project_tasks.check_stalled_projects")
def check_stalled_projects():
    """
    Periodic task to check for stalled projects.

    Checks for projects in IN_PROGRESS status that haven't
    been updated in over 2 hours.
    """
    logger.info("Checking for stalled projects...")

    try:
        stalled = asyncio.run(_check_stalled_internal())

        if stalled:
            logger.warning(f"Found {len(stalled)} stalled projects: {stalled}")
        else:
            logger.info("No stalled projects found")

        return {"stalled_projects": stalled}

    except Exception as e:
        logger.error(f"Error checking stalled projects: {e}", exc_info=True)
        return {"error": str(e)}


async def _check_stalled_internal():
    """Internal async function to check stalled projects."""
    stalled_projects = []

    async with get_db() as db:
        # Find projects in progress for > 2 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=2)

        result = await db.execute(
            select(Project).where(
                Project.status == ProjectStatus.IN_PROGRESS,
                Project.updated_at < cutoff_time
            )
        )

        projects = result.scalars().all()

        for project in projects:
            stalled_projects.append({
                "id": str(project.id),
                "name": project.name,
                "updated_at": project.updated_at.isoformat(),
            })

            # Mark as failed
            project.status = ProjectStatus.FAILED

            if not project.project_metadata:
                project.project_metadata = {}

            project.project_metadata["stalled"] = True
            project.project_metadata["stalled_at"] = datetime.utcnow().isoformat()

        await db.commit()

    return stalled_projects


@celery_app.task(name="app.tasks.project_tasks.cleanup_old_projects")
def cleanup_old_projects(days: int = 90):
    """
    Cleanup old completed/failed projects.

    Args:
        days: Remove projects older than this many days

    Returns:
        Number of projects cleaned up
    """
    logger.info(f"Cleaning up projects older than {days} days...")

    try:
        count = asyncio.run(_cleanup_old_projects_internal(days))

        logger.info(f"Cleaned up {count} old projects")

        return {"cleaned_up": count}

    except Exception as e:
        logger.error(f"Error cleaning up old projects: {e}", exc_info=True)
        return {"error": str(e)}


async def _cleanup_old_projects_internal(days: int):
    """Internal async function to cleanup old projects."""
    async with get_db() as db:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Find old completed/failed projects
        result = await db.execute(
            select(Project).where(
                Project.status.in_([ProjectStatus.COMPLETED, ProjectStatus.FAILED]),
                Project.updated_at < cutoff_date
            )
        )

        projects = result.scalars().all()
        count = len(projects)

        for project in projects:
            await db.delete(project)

        await db.commit()

    return count
