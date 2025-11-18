"""
Celery Tasks for Analytics and Monitoring

Background tasks for metrics, analytics, and cleanup operations.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, func

from app.celery_app import celery_app
from app.database.connection import get_db
from app.models.agent_execution import AgentExecution
from app.models.agent_analytics import AgentPerformanceMetric
from app.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.analytics_tasks.update_agent_metrics")
def update_agent_metrics():
    """
    Periodic task to update agent performance metrics.

    Runs hourly to calculate and store performance metrics for each agent.
    """
    logger.info("Updating agent performance metrics...")

    try:
        metrics = asyncio.run(_update_metrics_internal())

        logger.info(f"Updated metrics for {len(metrics)} agents")

        return {"updated_agents": metrics}

    except Exception as e:
        logger.error(f"Error updating agent metrics: {e}", exc_info=True)
        return {"error": str(e)}


async def _update_metrics_internal():
    """Internal async function to update metrics."""
    updated_agents = []

    async with get_db() as db:
        # Get all agent types with executions
        result = await db.execute(
            select(AgentExecution.agent_type, func.count().label("count"))
            .group_by(AgentExecution.agent_type)
        )

        agent_types = result.all()

        for agent_type, _ in agent_types:
            # Calculate metrics for this agent
            execution_result = await db.execute(
                select(AgentExecution)
                .where(AgentExecution.agent_type == agent_type)
                .order_by(AgentExecution.created_at.desc())
                .limit(100)  # Last 100 executions
            )

            executions = execution_result.scalars().all()

            if not executions:
                continue

            # Calculate average tokens
            total_tokens = sum(e.tokens_used for e in executions if e.tokens_used)
            avg_tokens = total_tokens / len(executions) if executions else 0

            # Calculate success rate
            successful = sum(1 for e in executions if e.status == "completed")
            success_rate = (successful / len(executions) * 100) if executions else 0

            # Create or update metric
            metric = AgentPerformanceMetric(
                agent_type=agent_type,
                total_tasks=len(executions),
                successful_tasks=successful,
                failed_tasks=len(executions) - successful,
                avg_execution_time=30.0,  # Placeholder
                total_tokens_used=total_tokens,
                success_rate=success_rate,
                analytics_metadata={
                    "avg_tokens_per_task": avg_tokens,
                    "period": "last_100_executions",
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )

            db.add(metric)
            updated_agents.append(agent_type)

        await db.commit()

    return updated_agents


@celery_app.task(name="app.tasks.analytics_tasks.cleanup_old_executions")
def cleanup_old_executions(days: int = 30):
    """
    Cleanup old agent executions.

    Args:
        days: Remove executions older than this many days

    Returns:
        Number of executions cleaned up
    """
    logger.info(f"Cleaning up executions older than {days} days...")

    try:
        count = asyncio.run(_cleanup_executions_internal(days))

        logger.info(f"Cleaned up {count} old executions")

        return {"cleaned_up": count}

    except Exception as e:
        logger.error(f"Error cleaning up executions: {e}", exc_info=True)
        return {"error": str(e)}


async def _cleanup_executions_internal(days: int):
    """Internal async function to cleanup old executions."""
    async with get_db() as db:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Find old executions
        result = await db.execute(
            select(AgentExecution).where(
                AgentExecution.created_at < cutoff_date
            )
        )

        executions = result.scalars().all()
        count = len(executions)

        for execution in executions:
            await db.delete(execution)

        await db.commit()

    return count


@celery_app.task(name="app.tasks.analytics_tasks.generate_daily_report")
def generate_daily_report():
    """
    Generate daily analytics report.

    Aggregates metrics for the past 24 hours.
    """
    logger.info("Generating daily report...")

    try:
        report = asyncio.run(_generate_report_internal())

        logger.info("Daily report generated successfully")

        return report

    except Exception as e:
        logger.error(f"Error generating daily report: {e}", exc_info=True)
        return {"error": str(e)}


async def _generate_report_internal():
    """Internal async function to generate report."""
    async with get_db() as db:
        # Get stats for last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)

        # Task stats
        task_result = await db.execute(
            select(
                func.count(Task.id).label("total"),
                func.count(Task.id).filter(Task.status == TaskStatus.COMPLETED).label("completed"),
                func.count(Task.id).filter(Task.status == TaskStatus.FAILED).label("failed"),
            )
            .where(Task.created_at >= yesterday)
        )

        task_stats = task_result.first()

        # Agent execution stats
        exec_result = await db.execute(
            select(
                func.count(AgentExecution.id).label("total"),
                func.sum(AgentExecution.tokens_used).label("total_tokens"),
            )
            .where(AgentExecution.created_at >= yesterday)
        )

        exec_stats = exec_result.first()

        report = {
            "date": datetime.utcnow().date().isoformat(),
            "tasks": {
                "total": task_stats.total or 0,
                "completed": task_stats.completed or 0,
                "failed": task_stats.failed or 0,
            },
            "executions": {
                "total": exec_stats.total or 0,
                "total_tokens": exec_stats.total_tokens or 0,
            },
        }

    return report
