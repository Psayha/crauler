from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from .base import Base, TimestampMixin


class AgentExecution(Base, TimestampMixin):
    """Agent execution tracking model"""

    __tablename__ = "agent_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)

    agent_type = Column(String(100), nullable=False)
    prompt = Column(Text)
    response = Column(Text)

    tokens_used = Column(Integer, default=0)
    execution_time_ms = Column(Integer, default=0)

    status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)

    metadata = Column(JSONB, default={})

    # Relationships
    task = relationship("Task", back_populates="executions")

    def __repr__(self):
        return f"<AgentExecution {self.agent_type} for task {self.task_id}>"
