"""
Knowledge Base Service

Handles semantic search, embedding generation, and knowledge storage.
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from anthropic import AsyncAnthropic

from app.models.knowledge import KnowledgeEntry, SearchQuery
from app.config import settings
from app.database.connection import get_db

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Service for knowledge base operations.

    Features:
    - Embedding generation using Claude API
    - Semantic search with pgvector
    - Knowledge storage and retrieval
    - Similar document finding
    """

    def __init__(self):
        """Initialize knowledge service."""
        self.client = AsyncAnthropic(api_key=settings.claude_api_key)
        logger.info("KnowledgeService initialized")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.

        Currently returns a placeholder. In production, you would:
        1. Use Claude API's embedding endpoint (when available)
        2. Or use OpenAI's ada-002 model
        3. Or use local embedding models like sentence-transformers

        Args:
            text: Text to embed

        Returns:
            1536-dimensional embedding vector
        """
        # Placeholder implementation
        # TODO: Replace with actual embedding generation
        # For now, return a random normalized vector
        import random
        import math

        vector = [random.gauss(0, 1) for _ in range(1536)]
        magnitude = math.sqrt(sum(x * x for x in vector))
        normalized = [x / magnitude for x in vector]

        return normalized

    async def store_knowledge(
        self,
        title: str,
        content: str,
        content_type: str,
        source_type: Optional[str] = None,
        source_id: Optional[UUID] = None,
        agent_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None,
    ) -> KnowledgeEntry:
        """
        Store knowledge with embedding.

        Args:
            title: Knowledge title
            content: Knowledge content
            content_type: Type of content
            source_type: Source type (project, task, etc.)
            source_id: Source UUID
            agent_type: Agent that created this
            tags: Tags for categorization
            metadata: Additional metadata
            db: Database session

        Returns:
            Created knowledge entry
        """
        logger.info(f"Storing knowledge: {title[:50]}...")

        # Generate embedding
        embedding = await self.generate_embedding(content)

        # Count tokens (rough estimate)
        token_count = len(content.split())

        # Create entry
        entry = KnowledgeEntry(
            title=title,
            content=content,
            content_type=content_type,
            embedding=embedding,
            source_type=source_type,
            source_id=source_id,
            agent_type=agent_type,
            tags=tags or [],
            knowledge_metadata=metadata or {},
            token_count=token_count,
        )

        should_close_db = False
        if db is None:
            db = await anext(get_db())
            should_close_db = True

        try:
            db.add(entry)
            await db.commit()
            await db.refresh(entry)

            logger.info(f"Knowledge stored: {entry.id}")

            return entry

        finally:
            if should_close_db:
                await db.close()

    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        content_type: Optional[str] = None,
        agent_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        db: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search.

        Args:
            query: Search query text
            top_k: Number of results to return
            content_type: Filter by content type
            agent_type: Filter by agent type
            tags: Filter by tags
            db: Database session

        Returns:
            List of matching knowledge entries with relevance scores
        """
        logger.info(f"Semantic search: {query[:50]}...")

        # Generate query embedding
        query_embedding = await self.generate_embedding(query)

        should_close_db = False
        if db is None:
            db = await anext(get_db())
            should_close_db = True

        try:
            # Build query
            stmt = select(
                KnowledgeEntry,
                KnowledgeEntry.embedding.cosine_distance(query_embedding).label(
                    "distance"
                ),
            )

            # Apply filters
            if content_type:
                stmt = stmt.where(KnowledgeEntry.content_type == content_type)

            if agent_type:
                stmt = stmt.where(KnowledgeEntry.agent_type == agent_type)

            if tags:
                stmt = stmt.where(KnowledgeEntry.tags.overlap(tags))

            # Order by similarity and limit
            stmt = stmt.order_by("distance").limit(top_k)

            result = await db.execute(stmt)
            rows = result.all()

            # Format results
            results = []
            for entry, distance in rows:
                result_dict = entry.to_dict()
                result_dict["relevance_score"] = 1 - distance  # Convert distance to similarity
                results.append(result_dict)

            logger.info(f"Found {len(results)} results")

            # Log search query
            await self._log_search_query(query, query_embedding, len(results), db)

            return results

        finally:
            if should_close_db:
                await db.close()

    async def find_similar(
        self,
        entry_id: UUID,
        top_k: int = 5,
        db: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find similar knowledge entries.

        Args:
            entry_id: Knowledge entry UUID
            top_k: Number of similar entries to return
            db: Database session

        Returns:
            List of similar entries with relevance scores
        """
        should_close_db = False
        if db is None:
            db = await anext(get_db())
            should_close_db = True

        try:
            # Get the entry
            entry_result = await db.execute(
                select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id)
            )
            entry = entry_result.scalar_one_or_none()

            if not entry:
                return []

            # Find similar entries
            stmt = (
                select(
                    KnowledgeEntry,
                    KnowledgeEntry.embedding.cosine_distance(entry.embedding).label(
                        "distance"
                    ),
                )
                .where(KnowledgeEntry.id != entry_id)
                .order_by("distance")
                .limit(top_k)
            )

            result = await db.execute(stmt)
            rows = result.all()

            # Format results
            results = []
            for similar_entry, distance in rows:
                result_dict = similar_entry.to_dict()
                result_dict["relevance_score"] = 1 - distance
                results.append(result_dict)

            return results

        finally:
            if should_close_db:
                await db.close()

    async def get_context_for_agent(
        self,
        agent_type: str,
        query: str,
        top_k: int = 3,
        db: Optional[AsyncSession] = None,
    ) -> str:
        """
        Get relevant context for an agent's task.

        Args:
            agent_type: Type of agent
            query: Task description or query
            top_k: Number of context entries
            db: Database session

        Returns:
            Formatted context string
        """
        results = await self.semantic_search(
            query=query,
            top_k=top_k,
            agent_type=agent_type,
            db=db,
        )

        if not results:
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"--- Context {i} (relevance: {result['relevance_score']:.2f}) ---\n"
                f"{result['content']}\n"
            )

        return "\n".join(context_parts)

    async def suggest_similar_projects(
        self,
        project_description: str,
        top_k: int = 5,
        db: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """
        Suggest similar past projects.

        Args:
            project_description: New project description
            top_k: Number of suggestions
            db: Database session

        Returns:
            List of similar projects
        """
        return await self.semantic_search(
            query=project_description,
            top_k=top_k,
            content_type="project_output",
            db=db,
        )

    async def _log_search_query(
        self,
        query_text: str,
        query_embedding: List[float],
        results_count: int,
        db: AsyncSession,
    ):
        """Log search query for analytics."""
        try:
            search_query = SearchQuery(
                query_text=query_text,
                query_embedding=query_embedding,
                results_count=results_count,
            )

            db.add(search_query)
            await db.commit()

        except Exception as e:
            logger.warning(f"Failed to log search query: {e}")


# Global instance
knowledge_service = KnowledgeService()
