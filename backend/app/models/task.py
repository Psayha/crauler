from sqlalchemy import Column, String, Text, ForeignKey, Integer, Enum as SQLEnum, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from .base import Base, TimestampMixin


class TaskStatus(str, enum.Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskPriority(str, enum.Enum):
    """Task priority enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Task(Base, TimestampMixin):
    """Task model"""

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)

    title = Column(String(255), nullable=False)
    description = Column(Text)
    assigned_agent = Column(String(100))  # agent type: marketing, frontend_developer, etc

    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.NORMAL, nullable=False)

    task_type = Column(String(100))
    input_data = Column(JSONB, default={})
    output_data = Column(JSONB, default={})

    dependencies = Column(ARRAY(UUID(as_uuid=True)), default=[])

    estimated_tokens = Column(Integer, default=0)
    actual_tokens = Column(Integer, default=0)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    subtasks = relationship("Task", backref="parent_task", remote_side=[id])
    executions = relationship("AgentExecution", back_populates="task")

    def __repr__(self):
        return f"<Task {self.title} ({self.status.value})>"
