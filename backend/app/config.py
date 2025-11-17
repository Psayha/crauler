from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""

    # App
    app_name: str = "AI Agency"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = "change-this-secret-key"

    # Database
    database_url: str = "postgresql+asyncpg://aiagency:securepassword@localhost:5432/ai_agency"
    redis_url: str = "redis://localhost:6379"

    # Claude API
    claude_api_key: str
    claude_model: str = "claude-3-opus-20240229"
    claude_max_tokens: int = 4000
    claude_temperature: float = 0.3

    # Vector DB (Pinecone)
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    pinecone_index: Optional[str] = None

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Monitoring
    sentry_dsn: Optional[str] = None

    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:8000"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
