"""
Knowledge Base Models

Models for semantic search and knowledge storage using pgvector.
"""

from sqlalchemy import Column, String, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from pgvector.sqlalchemy import Vector
import uuid

from .base import Base, TimestampMixin


class KnowledgeEntry(Base, TimestampMixin):
    """
    Knowledge Base Entry with semantic embeddings.

    Stores project results, task outputs, and other knowledge
    with vector embeddings for semantic search.
    """

    __tablename__ = "knowledge_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Content
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(50))  # 'task_result', 'project_output', 'documentation', etc.

    # Vector embedding (1536 dimensions for OpenAI ada-002 or Claude embeddings)
    embedding = Column(Vector(1536))

    # Source information
    source_type = Column(String(50))  # 'project', 'task', 'agent_execution'
    source_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    agent_type = Column(String(100), nullable=True, index=True)

    # Metadata
    tags = Column(ARRAY(String), default=[])
    knowledge_metadata = Column(JSONB, default={})

    # Search optimization
    token_count = Column(Integer, default=0)
    relevance_score = Column(Float, default=0.0)

    def __repr__(self):
        return f"<KnowledgeEntry {self.title[:50]}>"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "content": self.content,
            "content_type": self.content_type,
            "source_type": self.source_type,
            "source_id": str(self.source_id) if self.source_id else None,
            "agent_type": self.agent_type,
            "tags": self.tags,
            "metadata": self.knowledge_metadata,
            "token_count": self.token_count,
            "relevance_score": self.relevance_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SearchQuery(Base, TimestampMixin):
    """
    Log of search queries for analytics.

    Tracks what users search for to improve recommendations.
    """

    __tablename__ = "search_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(1536))

    # Context
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Results
    results_count = Column(Integer, default=0)
    top_result_id = Column(UUID(as_uuid=True), nullable=True)

    # Metadata
    search_metadata = Column(JSONB, default={})

    def __repr__(self):
        return f"<SearchQuery {self.query_text[:50]}>"
