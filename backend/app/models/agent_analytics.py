"""Models for HR Agent analytics and agent management."""
from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from .base import Base, TimestampMixin


class AgentPerformanceMetric(Base, TimestampMixin):
    """
    Agent performance metrics tracking.
    Stores various metrics for each agent over time.
    """

    __tablename__ = "agent_performance_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type = Column(String(100), nullable=False, index=True)

    # Metric information
    metric_type = Column(String(50), nullable=False)  # success_rate, avg_time, quality_score, token_efficiency
    metric_value = Column(Float, nullable=False)

    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Additional context
    total_tasks = Column(Integer, default=0)
    successful_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    avg_execution_time_ms = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)

    # Metadata
    analytics_metadata = Column(JSONB, default={})  # Renamed from 'metadata' - SQLAlchemy reserved

    def __repr__(self):
        return f"<AgentPerformanceMetric {self.agent_type} ({self.metric_type}: {self.metric_value})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_type": self.agent_type,
            "metric_type": self.metric_type,
            "metric_value": self.metric_value,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "avg_execution_time_ms": self.avg_execution_time_ms,
            "total_tokens_used": self.total_tokens_used,
            "metadata": self.analytics_metadata,  # Use renamed column
            "created_at": self.created_at.isoformat(),
        }


class AgentImprovement(Base, TimestampMixin):
    """
    Agent improvement history.
    Tracks changes and improvements to agent configurations.
    """

    __tablename__ = "agent_improvements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type = Column(String(100), nullable=False, index=True)

    # Improvement information
    improvement_type = Column(String(50), nullable=False)  # prompt_update, temperature_change, system_update
    description = Column(Text)

    # Configuration changes
    previous_config = Column(JSONB, default={})
    new_config = Column(JSONB, default={})

    # Test results
    test_results = Column(JSONB, default={})
    performance_impact = Column(Float)  # Percentage change in performance

    # Status
    status = Column(String(20), default="proposed")  # proposed, testing, approved, rejected, active, deprecated

    # Approval
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Metadata
    analytics_metadata = Column(JSONB, default={})  # Renamed from 'metadata' - SQLAlchemy reserved

    def __repr__(self):
        return f"<AgentImprovement {self.agent_type} ({self.improvement_type}: {self.status})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_type": self.agent_type,
            "improvement_type": self.improvement_type,
            "description": self.description,
            "previous_config": self.previous_config,
            "new_config": self.new_config,
            "test_results": self.test_results,
            "performance_impact": self.performance_impact,
            "status": self.status,
            "approved_by": str(self.approved_by) if self.approved_by else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "metadata": self.analytics_metadata,  # Use renamed column
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class DynamicAgent(Base, TimestampMixin):
    """
    Dynamically created agents.
    Agents created by HR Agent based on project needs.
    """

    __tablename__ = "dynamic_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Agent identification
    agent_type = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Configuration
    system_prompt = Column(Text, nullable=False)
    temperature = Column(Float, default=0.5)
    max_tokens = Column(Integer, default=4000)

    # Expertise and capabilities
    expertise = Column(ARRAY(String), default=[])
    capabilities = Column(JSONB, default={})

    # Creation context
    created_by_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    creation_reason = Column(Text)

    # Validation and performance
    validation_score = Column(Float, default=0.0)
    validation_details = Column(JSONB, default={})

    # Usage statistics
    status = Column(String(20), default="testing")  # testing, active, deprecated, archived
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_quality_score = Column(Float, default=0.0)

    # Lifecycle
    activated_at = Column(DateTime, nullable=True)
    deprecated_at = Column(DateTime, nullable=True)

    # Metadata
    analytics_metadata = Column(JSONB, default={})  # Renamed from 'metadata' - SQLAlchemy reserved

    # Relationships
    created_by_project = relationship("Project", foreign_keys=[created_by_project_id])
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])

    def __repr__(self):
        return f"<DynamicAgent {self.name} ({self.agent_type}: {self.status})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_type": self.agent_type,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "expertise": self.expertise,
            "capabilities": self.capabilities,
            "created_by_project_id": str(self.created_by_project_id) if self.created_by_project_id else None,
            "created_by_user_id": str(self.created_by_user_id) if self.created_by_user_id else None,
            "creation_reason": self.creation_reason,
            "validation_score": self.validation_score,
            "validation_details": self.validation_details,
            "status": self.status,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "avg_quality_score": self.avg_quality_score,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "metadata": self.analytics_metadata,  # Use renamed column
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
