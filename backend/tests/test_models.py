"""Test database models."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models.user import User, UserSettings, Notification
from app.models.organization import Organization
from app.models.project import Project, ProjectType, ProjectStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.agent_execution import AgentExecution


def test_import_all_models():
    """Test all models can be imported."""
    assert User is not None
    assert UserSettings is not None
    assert Notification is not None
    assert Organization is not None
    assert Project is not None
    assert Task is not None
    assert AgentExecution is not None


def test_project_enums():
    """Test project enums are defined correctly."""
    assert hasattr(ProjectType, "WEBSITE")
    assert hasattr(ProjectType, "MOBILE_APP")
    assert hasattr(ProjectType, "MARKETING_CAMPAIGN")

    assert hasattr(ProjectStatus, "DRAFT")
    assert hasattr(ProjectStatus, "IN_PROGRESS")
    assert hasattr(ProjectStatus, "COMPLETED")


def test_task_enums():
    """Test task enums are defined correctly."""
    assert hasattr(TaskStatus, "PENDING")
    assert hasattr(TaskStatus, "IN_PROGRESS")
    assert hasattr(TaskStatus, "COMPLETED")
    assert hasattr(TaskStatus, "FAILED")

    assert hasattr(TaskPriority, "CRITICAL")
    assert hasattr(TaskPriority, "HIGH")
    assert hasattr(TaskPriority, "NORMAL")
    assert hasattr(TaskPriority, "LOW")


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Test creating a user."""
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        credits_balance=100,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.telegram_id == 123456789
    assert user.username == "testuser"
    assert user.credits_balance == 100


@pytest.mark.asyncio
async def test_create_organization(db_session: AsyncSession):
    """Test creating an organization."""
    org = Organization(
        name="Test Org",
        slug="test-org",
        plan="starter",
        credits_balance=1000,
    )

    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    assert org.id is not None
    assert org.name == "Test Org"
    assert org.slug == "test-org"
    assert org.credits_balance == 1000


@pytest.mark.asyncio
async def test_user_to_dict(db_session: AsyncSession):
    """Test user to_dict method."""
    user = User(
        telegram_id=987654321,
        username="dictuser",
        first_name="Dict",
        is_premium=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    user_dict = user.to_dict()

    assert isinstance(user_dict, dict)
    assert "id" in user_dict
    assert "telegram_id" in user_dict
    assert user_dict["telegram_id"] == 987654321
    assert user_dict["username"] == "dictuser"
    assert user_dict["is_premium"] is True
