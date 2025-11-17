"""HR Agent API endpoints for agent management and analytics."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.database.connection import get_db_session
from app.models.agent_analytics import (
    AgentPerformanceMetric,
    AgentImprovement,
    DynamicAgent,
)
from app.models.agent_execution import AgentExecution
from app.models.task import Task, TaskStatus
from app.agents.base_agent import AgentRegistry
from app.agents.hr_agent import HRAgent
from pydantic import BaseModel


router = APIRouter()


# Pydantic models for request/response
class PerformanceAnalysisRequest(BaseModel):
    agent_type: str
    time_period: str = "30d"


class ImprovementSuggestionRequest(BaseModel):
    agent_type: str
    issues: List[str]


class SkillGapAnalysisRequest(BaseModel):
    project_description: str
    task_breakdown: List[dict]


class NewAgentRequest(BaseModel):
    agent_type: str
    required_skills: List[str]
    context: str


@router.get("/agents/performance")
async def list_agent_performance(
    time_period: str = "30d",
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get performance metrics for all agents.
    """
    # Calculate time range
    days = int(time_period.replace("d", ""))
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get all agents
    registry = AgentRegistry()
    agent_types = list(registry.agents.keys())

    performance_data = []

    for agent_type in agent_types:
        # Count executions
        result = await db.execute(
            select(func.count(AgentExecution.id))
            .join(Task)
            .where(
                and_(
                    Task.assigned_agent == agent_type,
                    AgentExecution.created_at >= start_date
                )
            )
        )
        total_executions = result.scalar() or 0

        # Count successful executions
        result = await db.execute(
            select(func.count(AgentExecution.id))
            .join(Task)
            .where(
                and_(
                    Task.assigned_agent == agent_type,
                    Task.status == TaskStatus.COMPLETED,
                    AgentExecution.created_at >= start_date
                )
            )
        )
        successful_executions = result.scalar() or 0

        # Calculate success rate
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0

        # Get average execution time
        result = await db.execute(
            select(func.avg(AgentExecution.execution_time_ms))
            .join(Task)
            .where(
                and_(
                    Task.assigned_agent == agent_type,
                    AgentExecution.created_at >= start_date
                )
            )
        )
        avg_time = result.scalar() or 0

        # Get total tokens
        result = await db.execute(
            select(func.sum(AgentExecution.tokens_used))
            .join(Task)
            .where(
                and_(
                    Task.assigned_agent == agent_type,
                    AgentExecution.created_at >= start_date
                )
            )
        )
        total_tokens = result.scalar() or 0

        performance_data.append({
            "agent_type": agent_type,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": round(success_rate, 2),
            "avg_execution_time_ms": round(avg_time, 2),
            "total_tokens_used": total_tokens,
        })

    return {
        "time_period": time_period,
        "agents": performance_data,
        "total_agents": len(agent_types)
    }


@router.get("/agents/{agent_type}/performance")
async def get_agent_performance(
    agent_type: str,
    time_period: str = "30d",
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get detailed performance metrics for a specific agent.
    """
    # Verify agent exists
    registry = AgentRegistry()
    if agent_type not in registry.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found")

    # Calculate time range
    days = int(time_period.replace("d", ""))
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get execution statistics
    result = await db.execute(
        select(
            func.count(AgentExecution.id).label("total"),
            func.avg(AgentExecution.execution_time_ms).label("avg_time"),
            func.sum(AgentExecution.tokens_used).label("total_tokens")
        )
        .join(Task)
        .where(
            and_(
                Task.assigned_agent == agent_type,
                AgentExecution.created_at >= start_date
            )
        )
    )
    stats = result.first()

    # Get status breakdown
    result = await db.execute(
        select(Task.status, func.count(Task.id))
        .where(
            and_(
                Task.assigned_agent == agent_type,
                Task.created_at >= start_date
            )
        )
        .group_by(Task.status)
    )
    status_breakdown = {status.value: count for status, count in result.all()}

    return {
        "agent_type": agent_type,
        "time_period": time_period,
        "total_executions": stats.total or 0,
        "avg_execution_time_ms": round(stats.avg_time or 0, 2),
        "total_tokens_used": stats.total_tokens or 0,
        "status_breakdown": status_breakdown,
    }


@router.post("/agents/{agent_type}/analyze")
async def analyze_agent(
    agent_type: str,
    request: PerformanceAnalysisRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Analyze agent performance using HR Agent.
    """
    # Verify agent exists
    registry = AgentRegistry()
    if agent_type not in registry.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found")

    # Get performance metrics
    performance_data = await get_agent_performance(agent_type, request.time_period, db)

    # Use HR Agent to analyze
    hr_agent = HRAgent()
    analysis = await hr_agent.analyze_agent_performance(
        agent_type=agent_type,
        metrics=performance_data,
        time_period=request.time_period
    )

    return {
        "agent_type": agent_type,
        "analysis": analysis,
        "analyzed_at": datetime.utcnow().isoformat()
    }


@router.post("/agents/{agent_type}/suggest-improvements")
async def suggest_improvements(
    agent_type: str,
    request: ImprovementSuggestionRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get improvement suggestions for an agent.
    """
    # Verify agent exists
    registry = AgentRegistry()
    if agent_type not in registry.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found")

    agent = registry.agents[agent_type]

    # Get current configuration
    current_config = {
        "agent_type": agent.get_agent_type(),
        "temperature": agent.get_temperature(),
        "system_prompt": agent.get_system_prompt()[:500] + "...",  # First 500 chars
    }

    # Use HR Agent to suggest improvements
    hr_agent = HRAgent()
    suggestions = await hr_agent.suggest_improvements(
        agent_type=agent_type,
        current_config=current_config,
        performance_issues=request.issues
    )

    return {
        "agent_type": agent_type,
        "current_config": current_config,
        "suggestions": suggestions,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/improvements")
async def list_improvements(
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    List agent improvements.
    """
    query = select(AgentImprovement)

    if agent_type:
        query = query.where(AgentImprovement.agent_type == agent_type)
    if status:
        query = query.where(AgentImprovement.status == status)

    query = query.order_by(AgentImprovement.created_at.desc())

    result = await db.execute(query)
    improvements = result.scalars().all()

    return {
        "improvements": [imp.to_dict() for imp in improvements],
        "total": len(improvements)
    }


@router.post("/analyze-skill-gaps")
async def analyze_skill_gaps(
    request: SkillGapAnalysisRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Analyze skill gaps for a project.
    """
    # Get current agents
    registry = AgentRegistry()
    current_agents = list(registry.agents.keys())

    # Use HR Agent to analyze
    hr_agent = HRAgent()
    analysis = await hr_agent.identify_skill_gaps(
        project_description=request.project_description,
        current_agents=current_agents,
        task_breakdown=request.task_breakdown
    )

    return {
        "project_description": request.project_description,
        "current_agents": current_agents,
        "analysis": analysis,
        "analyzed_at": datetime.utcnow().isoformat()
    }


@router.post("/recruit-agent")
async def recruit_new_agent(
    request: NewAgentRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Design a new specialized agent.
    """
    # Check if agent type already exists
    registry = AgentRegistry()
    if request.agent_type in registry.agents:
        raise HTTPException(
            status_code=400,
            detail=f"Agent type {request.agent_type} already exists"
        )

    # Use HR Agent to design new agent
    hr_agent = HRAgent()
    agent_spec = await hr_agent.design_new_agent(
        agent_type=request.agent_type,
        required_skills=request.required_skills,
        project_context=request.context
    )

    # Create dynamic agent record
    dynamic_agent = DynamicAgent(
        agent_type=request.agent_type,
        name=agent_spec.get("name", request.agent_type),
        description=agent_spec.get("description", ""),
        system_prompt=agent_spec.get("system_prompt", ""),
        temperature=agent_spec.get("temperature", 0.5),
        max_tokens=agent_spec.get("max_tokens", 4000),
        expertise=agent_spec.get("expertise", []),
        capabilities=agent_spec.get("capabilities", {}),
        creation_reason=request.context,
        validation_score=0.0,
        status="testing"
    )

    db.add(dynamic_agent)
    await db.commit()
    await db.refresh(dynamic_agent)

    return {
        "agent_spec": agent_spec,
        "dynamic_agent": dynamic_agent.to_dict(),
        "created_at": datetime.utcnow().isoformat(),
        "next_steps": [
            "Test the agent with sample tasks",
            "Validate performance",
            "Approve for production use"
        ]
    }


@router.get("/dynamic-agents")
async def list_dynamic_agents(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    List dynamically created agents.
    """
    query = select(DynamicAgent)

    if status:
        query = query.where(DynamicAgent.status == status)

    query = query.order_by(DynamicAgent.created_at.desc())

    result = await db.execute(query)
    agents = result.scalars().all()

    return {
        "dynamic_agents": [agent.to_dict() for agent in agents],
        "total": len(agents)
    }


@router.get("/dynamic-agents/{agent_id}")
async def get_dynamic_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get details of a dynamic agent.
    """
    result = await db.execute(
        select(DynamicAgent).where(DynamicAgent.id == uuid.UUID(agent_id))
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Dynamic agent not found")

    return agent.to_dict()


@router.delete("/dynamic-agents/{agent_id}")
async def remove_dynamic_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Remove a dynamic agent.
    """
    result = await db.execute(
        select(DynamicAgent).where(DynamicAgent.id == uuid.UUID(agent_id))
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Dynamic agent not found")

    # Mark as archived instead of deleting
    agent.status = "archived"
    agent.deprecated_at = datetime.utcnow()

    await db.commit()

    return {
        "message": "Dynamic agent archived successfully",
        "agent_id": agent_id
    }
