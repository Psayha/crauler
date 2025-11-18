from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.database.connection import get_db
from app.models.project import Project, Task, AgentExecution
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def get_notifications(
    limit: int = 50,
    filter_type: Optional[str] = None,  # project, task, agent, system
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get activity notifications for the user
    Combines project updates, task completions, and agent activities
    """
    notifications = []

    # Get recent projects
    result = await db.execute(
        select(Project)
        .order_by(desc(Project.created_at))
        .limit(20)
    )
    projects = result.scalars().all()

    for project in projects:
        # Project created notification
        if not filter_type or filter_type == "project":
            notifications.append({
                "id": f"project-created-{project.id}",
                "type": "project_created",
                "title": "Проект создан",
                "message": project.description[:100] + "..." if len(project.description) > 100 else project.description,
                "project_id": str(project.id),
                "action_url": f"/projects/{project.id}",
                "created_at": project.created_at.isoformat(),
                "is_read": (datetime.utcnow() - project.created_at) > timedelta(days=1),
            })

        # Project completed notification
        if project.status == "completed" and (not filter_type or filter_type == "project"):
            notifications.append({
                "id": f"project-completed-{project.id}",
                "type": "project_completed",
                "title": "Проект завершён",
                "message": f"Все задачи проекта успешно выполнены",
                "project_id": str(project.id),
                "action_url": f"/projects/{project.id}",
                "created_at": project.updated_at.isoformat() if project.updated_at else project.created_at.isoformat(),
                "is_read": True,
            })

    # Get recent task executions
    result = await db.execute(
        select(AgentExecution)
        .order_by(desc(AgentExecution.created_at))
        .limit(30)
    )
    executions = result.scalars().all()

    for execution in executions:
        # Get task details
        task = await db.get(Task, execution.task_id)
        if not task:
            continue

        # Task completed notification
        if execution.status == "completed" and (not filter_type or filter_type in ["task", "agent"]):
            notifications.append({
                "id": f"task-completed-{execution.id}",
                "type": "agent_completed" if filter_type == "agent" else "task_completed",
                "title": f"{execution.agent_type.title().replace('_', ' ')} завершил задачу",
                "message": task.description[:100] + "..." if len(task.description) > 100 else task.description,
                "project_id": str(task.project_id),
                "action_url": f"/projects/{task.project_id}",
                "created_at": execution.updated_at.isoformat() if execution.updated_at else execution.created_at.isoformat(),
                "is_read": (datetime.utcnow() - (execution.updated_at or execution.created_at)) > timedelta(hours=6),
                "metadata": {
                    "agent_type": execution.agent_type,
                    "tokens_used": execution.tokens_used,
                },
            })

        # Task failed notification
        if execution.status == "failed" and (not filter_type or filter_type in ["task", "agent"]):
            notifications.append({
                "id": f"task-failed-{execution.id}",
                "type": "task_failed",
                "title": "Задача не выполнена",
                "message": f"{execution.agent_type.title().replace('_', ' ')} не смог выполнить задачу",
                "project_id": str(task.project_id),
                "action_url": f"/projects/{task.project_id}",
                "created_at": execution.updated_at.isoformat() if execution.updated_at else execution.created_at.isoformat(),
                "is_read": False,
                "metadata": {
                    "agent_type": execution.agent_type,
                    "error": execution.error_message,
                },
            })

    # Sort by created_at (newest first)
    notifications.sort(key=lambda x: x["created_at"], reverse=True)

    # Apply limit
    notifications = notifications[:limit]

    return {
        "notifications": notifications,
        "unread_count": sum(1 for n in notifications if not n["is_read"]),
        "total": len(notifications),
    }


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get count of unread notifications"""
    # Get recent projects and executions
    result = await db.execute(
        select(Project)
        .order_by(desc(Project.created_at))
        .limit(20)
    )
    projects = result.scalars().all()

    result = await db.execute(
        select(AgentExecution)
        .where(AgentExecution.status == "failed")
        .order_by(desc(AgentExecution.created_at))
        .limit(10)
    )
    failed_executions = result.scalars().all()

    # Count unread (created within last 24 hours or failed tasks)
    unread_count = 0
    for project in projects:
        if (datetime.utcnow() - project.created_at) < timedelta(hours=24):
            unread_count += 1

    unread_count += len(failed_executions)

    return {"unread_count": unread_count}
