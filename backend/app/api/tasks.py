from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy import select
import logging

from app.models.task import Task, TaskStatus
from app.database.connection import get_db
from app.services.agent_executor import agent_executor

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


@router.post("/{task_id}/execute")
async def execute_task(task_id: str) -> Dict[str, Any]:
    """
    Execute a single task with its assigned agent

    This endpoint will:
    1. Validate the task is ready (status = PENDING)
    2. Execute the task with the appropriate agent
    3. Update task status and save results
    """
    try:
        result = await agent_executor.execute_task(task_id)

        return {
            "message": "Task executed",
            "task_id": task_id,
            "result": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/retry")
async def retry_task(task_id: str) -> Dict[str, Any]:
    """
    Retry a failed task

    Only works for tasks with status = FAILED
    """
    try:
        result = await agent_executor.retry_task(task_id)

        return {
            "message": "Task retried",
            "task_id": task_id,
            "result": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to retry task: {e}")
        raise HTTPException(status_code=500, detail=str(e))
