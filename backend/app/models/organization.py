from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import Base, TimestampMixin


class Organization(Base, TimestampMixin):
    """Organization model for multi-tenancy"""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    plan = Column(String(50), default="starter")  # starter, business, enterprise
    credits_balance = Column(Integer, default=1000)

    # Relationships
    projects = relationship("Project", back_populates="organization")

    def __repr__(self):
        return f"<Organization {self.name}>"
