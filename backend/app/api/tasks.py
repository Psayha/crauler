from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import select
import logging

from app.models.task import Task, TaskStatus
from app.database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class TaskResponse(BaseModel):
    """Response schema for task"""

    id: str
    project_id: str
    title: str
    description: Optional[str]
    assigned_agent: str
    status: str
    priority: str
    estimated_tokens: int
    actual_tokens: int

    class Config:
        from_attributes = True


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task details"""
    try:
        async with get_db() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            return TaskResponse(
                id=str(task.id),
                project_id=str(task.project_id),
                title=task.title,
                description=task.description,
                assigned_agent=task.assigned_agent,
                status=task.status.value,
                priority=task.priority.value,
                estimated_tokens=task.estimated_tokens,
                actual_tokens=task.actual_tokens,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}", response_model=List[TaskResponse])
async def list_project_tasks(project_id: str):
    """List all tasks for a project"""
    try:
        async with get_db() as db:
            result = await db.execute(
                select(Task)
                .where(Task.project_id == project_id)
                .order_by(Task.created_at)
            )
            tasks = result.scalars().all()

            return [
                TaskResponse(
                    id=str(task.id),
                    project_id=str(task.project_id),
                    title=task.title,
                    description=task.description,
                    assigned_agent=task.assigned_agent,
                    status=task.status.value,
                    priority=task.priority.value,
                    estimated_tokens=task.estimated_tokens,
                    actual_tokens=task.actual_tokens,
                )
                for task in tasks
            ]

    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
