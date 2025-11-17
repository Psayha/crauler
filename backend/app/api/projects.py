from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import logging

from app.agents.orchestrator import orchestrator
from app.models.project import Project, ProjectStatus, ProjectType
from app.models.task import Task
from app.database.connection import get_db
from app.services.agent_executor import agent_executor

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class ProjectCreateRequest(BaseModel):
    """Request schema for creating project"""

    description: str
    organization_id: str


class TaskResponse(BaseModel):
    """Response schema for task"""

    id: str
    title: str
    description: Optional[str]
    assigned_agent: str
    status: str
    priority: str

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    """Response schema for project"""

    id: str
    name: str
    description: Optional[str]
    status: str
    type: str
    priority: str
    estimated_hours: Optional[int] = None

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    """Detailed project response with tasks"""

    tasks: List[TaskResponse] = []
    metadata: dict = {}

    class Config:
        from_attributes = True


@router.post("/", response_model=ProjectResponse)
async def create_project(request: ProjectCreateRequest):
    """
    Create new project

    This endpoint analyzes the project description, creates the project,
    and decomposes it into tasks automatically.
    """
    try:
        logger.info(
            f"Creating project for org {request.organization_id}: {request.description[:50]}..."
        )

        project = await orchestrator.create_project(
            request=request.description,
            organization_id=request.organization_id,
        )

        return ProjectResponse(
            id=str(project.id),
            name=project.name,
            description=project.description,
            status=project.status.value,
            type=project.type.value,
            priority=project.priority,
            estimated_hours=project.metadata.get("estimated_hours"),
        )

    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: str):
    """
    Get project details with tasks
    """
    try:
        async with get_db() as db:
            result = await db.execute(
                select(Project)
                .options(selectinload(Project.tasks))
                .where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            return ProjectDetailResponse(
                id=str(project.id),
                name=project.name,
                description=project.description,
                status=project.status.value,
                type=project.type.value,
                priority=project.priority,
                estimated_hours=project.metadata.get("estimated_hours"),
                tasks=[
                    TaskResponse(
                        id=str(task.id),
                        title=task.title,
                        description=task.description,
                        assigned_agent=task.assigned_agent,
                        status=task.status.value,
                        priority=task.priority.value,
                    )
                    for task in project.tasks
                ],
                metadata=project.metadata,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    organization_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    """
    List projects with optional filters
    """
    try:
        async with get_db() as db:
            query = select(Project)

            if organization_id:
                query = query.where(Project.organization_id == organization_id)

            if status:
                query = query.where(Project.status == status)

            query = query.limit(limit).order_by(Project.created_at.desc())

            result = await db.execute(query)
            projects = result.scalars().all()

            return [
                ProjectResponse(
                    id=str(p.id),
                    name=p.name,
                    description=p.description,
                    status=p.status.value,
                    type=p.type.value,
                    priority=p.priority,
                    estimated_hours=p.metadata.get("estimated_hours"),
                )
                for p in projects
            ]

    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/execute")
async def execute_project(project_id: str):
    """
    Start project execution

    This will:
    1. Validate project status
    2. Update to IN_PROGRESS
    3. Execute all tasks with agents in order
    4. Update project status based on results
    """
    try:
        async with get_db() as db:
            result = await db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            if project.status != ProjectStatus.PLANNING:
                raise HTTPException(
                    status_code=400,
                    detail=f"Project must be in PLANNING status, currently: {project.status.value}",
                )

            # Update status to in_progress
            project.status = ProjectStatus.IN_PROGRESS
            await db.commit()

            logger.info(f"Started execution of project {project_id}")

        # Execute project with agent executor
        execution_result = await agent_executor.execute_project(project_id)

        return {
            "status": "completed",
            "project_id": str(project_id),
            "message": "Project execution completed",
            "result": execution_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute project: {e}")
        raise HTTPException(status_code=500, detail=str(e))
