from sqlalchemy import Column, String, Text, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from .base import Base, TimestampMixin


class ProjectType(str, enum.Enum):
    """Project type enumeration"""
    WEBSITE = "website"
    MOBILE_APP = "mobile_app"
    MARKETING_CAMPAIGN = "marketing_campaign"
    DATA_ANALYSIS = "data_analysis"
    CONTENT_CREATION = "content_creation"
    CUSTOM = "custom"


class ProjectStatus(str, enum.Enum):
    """Project status enumeration"""
    DRAFT = "draft"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Project(Base, TimestampMixin):
    """Project model"""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False)
    type = Column(SQLEnum(ProjectType), nullable=False)
    priority = Column(String(20), default="normal")  # critical, high, normal, low
    deadline = Column(DateTime, nullable=True)
    metadata = Column(JSONB, default={})

    # Relationships
    organization = relationship("Organization", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.name} ({self.type.value})>"
