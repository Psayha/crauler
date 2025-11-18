"""
Tests for Task Execution System

Tests TaskExecutor service including:
- Task execution
- Dependency resolution
- Retry mechanism
- Error handling
- Rollback
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.executor import TaskExecutor, TaskExecutionError, DependencyError
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import Project, ProjectStatus, ProjectType
from app.models.agent_execution import AgentExecution


@pytest.fixture
def task_executor():
    """Create TaskExecutor instance."""
    return TaskExecutor(max_retries=2, retry_delay=1)


@pytest.fixture
async def sample_project(db_engine):
    """Create sample project."""
    from app.database.connection import get_db

    async with get_db() as db:
        project = Project(
            id=uuid4(),
            organization_id=uuid4(),  # Use UUID instead of string
            name="Test Project",
            description="Test project for task execution",
            type=ProjectType.WEBSITE,
            status=ProjectStatus.PLANNING,
            priority="normal",
            project_metadata={}
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project


@pytest.fixture
async def sample_task(db_engine, sample_project):
    """Create sample task."""
    from app.database.connection import get_db

    async with get_db() as db:
        task = Task(
            id=uuid4(),
            project_id=sample_project.id,
            title="Create homepage",
            description="Design and implement homepage",
            assigned_agent="frontend_developer",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            input_data={"requirements": ["responsive", "modern"]},
            estimated_tokens=1000,
            dependencies=[]
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task


@pytest.mark.asyncio
async def test_execute_task_success(task_executor, sample_task, db_engine):
    """Test successful task execution."""
    from app.database.connection import get_db

    # Mock agent execution
    with patch("app.agents.registry.get_agent") as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.execute.return_value = {
            "status": "success",
            "output": "Homepage created successfully",
            "tokens_used": 850
        }
        mock_get_agent.return_value = mock_agent

        async with get_db() as db:
            result = await task_executor.execute_task(sample_task.id, db)

        assert result["status"] == "success"
        assert result["task_id"] == str(sample_task.id)
        assert result["agent"] == "frontend_developer"
        assert "result" in result

        # Verify task status updated
        async with get_db() as db:
            updated_task = await task_executor._get_task(sample_task.id, db)
            assert updated_task.status == TaskStatus.COMPLETED
            assert updated_task.actual_tokens == 850


@pytest.mark.asyncio
async def test_execute_task_already_completed(task_executor, sample_task, db_engine):
    """Test execution of already completed task."""
    from app.database.connection import get_db

    # Mark task as completed
    async with get_db() as db:
        task = await task_executor._get_task(sample_task.id, db)
        task.status = TaskStatus.COMPLETED
        await db.commit()

    async with get_db() as db:
        result = await task_executor.execute_task(sample_task.id, db)

    assert result["status"] == "already_completed"


@pytest.mark.asyncio
async def test_execute_task_not_found(task_executor, db_engine):
    """Test execution of non-existent task."""
    from app.database.connection import get_db

    fake_task_id = uuid4()

    async with get_db() as db:
        with pytest.raises(TaskExecutionError, match="not found"):
            await task_executor.execute_task(fake_task_id, db)


@pytest.mark.asyncio
async def test_execute_task_with_dependencies_met(
    task_executor, sample_project, db_engine
):
    """Test task execution when dependencies are met."""
    from app.database.connection import get_db

    async with get_db() as db:
        # Create dependency task (completed)
        dep_task = Task(
            id=uuid4(),
            project_id=sample_project.id,
            title="Setup database",
            description="Initialize database",
            assigned_agent="backend_developer",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.HIGH,
            dependencies=[]
        )
        db.add(dep_task)

        # Create task with dependency
        task = Task(
            id=uuid4(),
            project_id=sample_project.id,
            title="Create API",
            description="Build REST API",
            assigned_agent="backend_developer",
            status=TaskStatus.PENDING,
            priority=TaskPriority.NORMAL,
            dependencies=[dep_task.id]
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        # Mock agent
        with patch("app.agents.registry.get_agent") as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.execute.return_value = {
                "status": "success",
                "output": "API created",
                "tokens_used": 1200
            }
            mock_get_agent.return_value = mock_agent

            result = await task_executor.execute_task(task.id, db)

        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_execute_task_with_dependencies_not_met(
    task_executor, sample_project, db_engine
):
    """Test task execution when dependencies are not met."""
    from app.database.connection import get_db

    async with get_db() as db:
        # Create dependency task (not completed)
        dep_task = Task(
            id=uuid4(),
            project_id=sample_project.id,
            title="Setup database",
            description="Initialize database",
            assigned_agent="backend_developer",
            status=TaskStatus.PENDING,  # Not completed!
            priority=TaskPriority.HIGH,
            dependencies=[]
        )
        db.add(dep_task)

        # Create task with dependency
        task = Task(
            id=uuid4(),
            project_id=sample_project.id,
            title="Create API",
            description="Build REST API",
            assigned_agent="backend_developer",
            status=TaskStatus.PENDING,
            priority=TaskPriority.NORMAL,
            dependencies=[dep_task.id]
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        with pytest.raises(DependencyError, match="incomplete dependencies"):
            await task_executor.execute_task(task.id, db)


@pytest.mark.asyncio
async def test_execute_task_with_retry(task_executor, sample_task, db_engine):
    """Test task execution with retry mechanism."""
    from app.database.connection import get_db

    # Mock agent to fail twice, then succeed
    with patch("app.agents.registry.get_agent") as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.execute.side_effect = [
            Exception("Temporary error"),
            Exception("Temporary error"),
            {
                "status": "success",
                "output": "Success on third attempt",
                "tokens_used": 900
            }
        ]
        mock_get_agent.return_value = mock_agent

        async with get_db() as db:
            result = await task_executor.execute_task(sample_task.id, db, retry_count=0)

        assert result["status"] == "success"
        assert mock_agent.execute.call_count == 3


@pytest.mark.asyncio
async def test_execute_task_max_retries_exceeded(task_executor, sample_task, db_engine):
    """Test task execution failing after max retries."""
    from app.database.connection import get_db

    # Mock agent to always fail
    with patch("app.agents.registry.get_agent") as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.execute.side_effect = Exception("Persistent error")
        mock_get_agent.return_value = mock_agent

        async with get_db() as db:
            with pytest.raises(TaskExecutionError, match="failed after"):
                await task_executor.execute_task(sample_task.id, db)

        # Verify task marked as failed
        async with get_db() as db:
            failed_task = await task_executor._get_task(sample_task.id, db)
            assert failed_task.status == TaskStatus.FAILED


@pytest.mark.asyncio
async def test_execute_task_agent_not_found(task_executor, sample_task, db_engine):
    """Test execution with non-existent agent."""
    from app.database.connection import get_db

    # Update task to use non-existent agent
    async with get_db() as db:
        task = await task_executor._get_task(sample_task.id, db)
        task.assigned_agent = "nonexistent_agent"
        await db.commit()

    with patch("app.agents.registry.get_agent", return_value=None):
        async with get_db() as db:
            with pytest.raises(TaskExecutionError, match="Agent .* not found"):
                await task_executor.execute_task(sample_task.id, db)


@pytest.mark.asyncio
async def test_execute_task_batch_parallel(task_executor, sample_project, db_engine):
    """Test batch execution in parallel mode."""
    from app.database.connection import get_db

    async with get_db() as db:
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task = Task(
                id=uuid4(),
                project_id=sample_project.id,
                title=f"Task {i}",
                description=f"Test task {i}",
                assigned_agent="frontend_developer",
                status=TaskStatus.PENDING,
                priority=TaskPriority.NORMAL
            )
            db.add(task)
            task_ids.append(task.id)

        await db.commit()

        # Mock agent
        with patch("app.agents.registry.get_agent") as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.execute.return_value = {
                "status": "success",
                "output": "Task completed",
                "tokens_used": 500
            }
            mock_get_agent.return_value = mock_agent

            results = await task_executor.execute_task_batch(
                task_ids, db, parallel=True
            )

        assert len(results) == 3
        for result in results:
            assert result["status"] == "success"


@pytest.mark.asyncio
async def test_execute_task_batch_sequential(task_executor, sample_project, db_engine):
    """Test batch execution in sequential mode."""
    from app.database.connection import get_db

    async with get_db() as db:
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task = Task(
                id=uuid4(),
                project_id=sample_project.id,
                title=f"Task {i}",
                description=f"Test task {i}",
                assigned_agent="backend_developer",
                status=TaskStatus.PENDING,
                priority=TaskPriority.NORMAL
            )
            db.add(task)
            task_ids.append(task.id)

        await db.commit()

        # Mock agent
        with patch("app.agents.registry.get_agent") as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.execute.return_value = {
                "status": "success",
                "output": "Task completed",
                "tokens_used": 600
            }
            mock_get_agent.return_value = mock_agent

            results = await task_executor.execute_task_batch(
                task_ids, db, parallel=False
            )

        assert len(results) == 3


@pytest.mark.asyncio
async def test_rollback_task(task_executor, sample_task, db_engine):
    """Test task rollback functionality."""
    from app.database.connection import get_db

    # First execute task
    async with get_db() as db:
        task = await task_executor._get_task(sample_task.id, db)
        task.status = TaskStatus.COMPLETED
        task.output_data = {"result": "completed"}
        task.actual_tokens = 1000
        await db.commit()

    # Now rollback
    async with get_db() as db:
        await task_executor.rollback_task(sample_task.id, db)

        # Verify task reset
        task = await task_executor._get_task(sample_task.id, db)
        assert task.status == TaskStatus.PENDING
        assert task.output_data == {}
        assert task.actual_tokens == 0


@pytest.mark.asyncio
async def test_execution_record_created(task_executor, sample_task, db_engine):
    """Test that execution record is created during task execution."""
    from app.database.connection import get_db
    from sqlalchemy import select

    with patch("app.agents.registry.get_agent") as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.execute.return_value = {
            "status": "success",
            "output": "Task completed",
            "tokens_used": 750
        }
        mock_get_agent.return_value = mock_agent

        async with get_db() as db:
            await task_executor.execute_task(sample_task.id, db)

            # Check execution record created
            result = await db.execute(
                select(AgentExecution).where(
                    AgentExecution.task_id == sample_task.id
                )
            )
            execution = result.scalar_one_or_none()

            assert execution is not None
            assert execution.agent_type == "frontend_developer"
            assert execution.status == "completed"
            assert execution.tokens_used == 750


@pytest.mark.asyncio
async def test_task_status_transitions(task_executor, sample_task, db_engine):
    """Test that task status transitions correctly during execution."""
    from app.database.connection import get_db

    statuses_observed = []

    async def mock_execute(*args, **kwargs):
        # Capture status during execution
        async with get_db() as db:
            task = await task_executor._get_task(sample_task.id, db)
            statuses_observed.append(task.status)

        return {
            "status": "success",
            "output": "Completed",
            "tokens_used": 800
        }

    with patch("app.agents.registry.get_agent") as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.execute = mock_execute
        mock_get_agent.return_value = mock_agent

        async with get_db() as db:
            await task_executor.execute_task(sample_task.id, db)

    # Should see IN_PROGRESS during execution
    assert TaskStatus.IN_PROGRESS in statuses_observed

    # Final status should be COMPLETED
    async with get_db() as db:
        final_task = await task_executor._get_task(sample_task.id, db)
        assert final_task.status == TaskStatus.COMPLETED
