from sqlalchemy import Column, String, BigInteger, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    User model for Telegram Mini App users
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), default="ru")
    is_premium = Column(Boolean, default=False)

    # Credits system for API usage
    credits_balance = Column(Integer, default=100)

    # Activity tracking
    last_active_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Additional user data from Telegram
    photo_url = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<User {self.telegram_id} (@{self.username})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "language_code": self.language_code,
            "is_premium": self.is_premium,
            "credits_balance": self.credits_balance,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "photo_url": self.photo_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class UserSettings(Base, TimestampMixin):
    """
    User settings and preferences
    """

    __tablename__ = "user_settings"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    theme = Column(String(20), default="auto")  # auto, light, dark
    language = Column(String(10), default="ru")
    notifications_enabled = Column(Boolean, default=True)
    auto_execute = Column(Boolean, default=False)  # Auto-start project execution

    # Additional settings as JSON
    settings = Column(JSONB, default={})

    def __repr__(self):
        return f"<UserSettings {self.user_id}>"

    def to_dict(self):
        return {
            "user_id": str(self.user_id),
            "theme": self.theme,
            "language": self.language,
            "notifications_enabled": self.notifications_enabled,
            "auto_execute": self.auto_execute,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Notification(Base, TimestampMixin):
    """
    User notifications
    """

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)

    type = Column(String(50), nullable=False)  # project_completed, task_failed, etc
    title = Column(String(255), nullable=False)
    message = Column(String, nullable=True)

    is_read = Column(Boolean, default=False)

    # Optional action data
    action_url = Column(String(500), nullable=True)
    notification_metadata = Column(JSONB, default={})  # Renamed from 'metadata' - SQLAlchemy reserved

    def __repr__(self):
        return f"<Notification {self.id} ({self.type})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "project_id": str(self.project_id) if self.project_id else None,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "action_url": self.action_url,
            "metadata": self.notification_metadata,  # Use renamed column
            "created_at": self.created_at.isoformat(),
        }
