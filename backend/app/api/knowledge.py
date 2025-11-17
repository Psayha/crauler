"""
Knowledge Base API Endpoints

Provides semantic search, knowledge storage, and context retrieval.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
import logging

from app.services.knowledge_service import knowledge_service
from app.database.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class KnowledgeCreateRequest(BaseModel):
    """Request schema for creating knowledge entry"""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    content_type: str = Field(..., description="Type: task_result, project_output, documentation, etc.")
    source_type: Optional[str] = Field(None, description="Source: project, task, agent_execution")
    source_id: Optional[UUID] = None
    agent_type: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SemanticSearchRequest(BaseModel):
    """Request schema for semantic search"""

    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    content_type: Optional[str] = None
    agent_type: Optional[str] = None
    tags: Optional[List[str]] = None


class ContextRequest(BaseModel):
    """Request schema for agent context"""

    agent_type: str
    query: str
    top_k: int = Field(default=3, ge=1, le=10)


class SimilarProjectsRequest(BaseModel):
    """Request schema for similar projects"""

    project_description: str
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeResponse(BaseModel):
    """Response schema for knowledge entry"""

    id: str
    title: str
    content: str
    content_type: str
    source_type: Optional[str]
    source_id: Optional[str]
    agent_type: Optional[str]
    tags: List[str]
    metadata: Dict[str, Any]
    token_count: int
    relevance_score: float
    created_at: Optional[str]

    class Config:
        from_attributes = True


class SearchResultResponse(BaseModel):
    """Response schema for search results"""

    results: List[KnowledgeResponse]
    total_count: int
    query: str


@router.post("/store", response_model=KnowledgeResponse)
async def store_knowledge(
    request: KnowledgeCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Store knowledge entry with embedding.

    Creates a new knowledge entry, generates embedding, and stores it
    in the vector database for semantic search.
    """
    try:
        logger.info(f"Storing knowledge: {request.title}")

        entry = await knowledge_service.store_knowledge(
            title=request.title,
            content=request.content,
            content_type=request.content_type,
            source_type=request.source_type,
            source_id=request.source_id,
            agent_type=request.agent_type,
            tags=request.tags,
            metadata=request.metadata,
            db=db,
        )

        return KnowledgeResponse(
            id=str(entry.id),
            title=entry.title,
            content=entry.content,
            content_type=entry.content_type,
            source_type=entry.source_type,
            source_id=str(entry.source_id) if entry.source_id else None,
            agent_type=entry.agent_type,
            tags=entry.tags,
            metadata=entry.knowledge_metadata,
            token_count=entry.token_count,
            relevance_score=entry.relevance_score,
            created_at=entry.created_at.isoformat() if entry.created_at else None,
        )

    except Exception as e:
        logger.error(f"Failed to store knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResultResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Perform semantic search on knowledge base.

    Uses vector embeddings and cosine distance to find semantically
    similar content.
    """
    try:
        logger.info(f"Semantic search: {request.query[:50]}...")

        results = await knowledge_service.semantic_search(
            query=request.query,
            top_k=request.top_k,
            content_type=request.content_type,
            agent_type=request.agent_type,
            tags=request.tags,
            db=db,
        )

        return SearchResultResponse(
            results=[
                KnowledgeResponse(
                    id=r["id"],
                    title=r["title"],
                    content=r["content"],
                    content_type=r["content_type"],
                    source_type=r["source_type"],
                    source_id=r["source_id"],
                    agent_type=r["agent_type"],
                    tags=r["tags"],
                    metadata=r["metadata"],
                    token_count=r["token_count"],
                    relevance_score=r["relevance_score"],
                    created_at=r["created_at"],
                )
                for r in results
            ],
            total_count=len(results),
            query=request.query,
        )

    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{entry_id}", response_model=List[KnowledgeResponse])
async def find_similar(
    entry_id: UUID,
    top_k: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """
    Find similar knowledge entries.

    Given a knowledge entry ID, finds the most similar entries
    based on vector similarity.
    """
    try:
        logger.info(f"Finding similar entries for {entry_id}")

        results = await knowledge_service.find_similar(
            entry_id=entry_id,
            top_k=top_k,
            db=db,
        )

        if not results:
            raise HTTPException(
                status_code=404,
                detail="Entry not found or no similar entries",
            )

        return [
            KnowledgeResponse(
                id=r["id"],
                title=r["title"],
                content=r["content"],
                content_type=r["content_type"],
                source_type=r["source_type"],
                source_id=r["source_id"],
                agent_type=r["agent_type"],
                tags=r["tags"],
                metadata=r["metadata"],
                token_count=r["token_count"],
                relevance_score=r["relevance_score"],
                created_at=r["created_at"],
            )
            for r in results
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to find similar entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context", response_model=str)
async def get_agent_context(
    request: ContextRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Get relevant context for agent task.

    Retrieves the most relevant knowledge entries for an agent's
    current task, formatted as context string.
    """
    try:
        logger.info(f"Getting context for {request.agent_type}: {request.query[:50]}...")

        context = await knowledge_service.get_context_for_agent(
            agent_type=request.agent_type,
            query=request.query,
            top_k=request.top_k,
            db=db,
        )

        return context

    except Exception as e:
        logger.error(f"Failed to get agent context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-projects", response_model=List[KnowledgeResponse])
async def suggest_similar_projects(
    request: SimilarProjectsRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Suggest similar past projects.

    Given a project description, finds similar projects that have
    been completed in the past for learning and reference.
    """
    try:
        logger.info(f"Suggesting projects for: {request.project_description[:50]}...")

        results = await knowledge_service.suggest_similar_projects(
            project_description=request.project_description,
            top_k=request.top_k,
            db=db,
        )

        return [
            KnowledgeResponse(
                id=r["id"],
                title=r["title"],
                content=r["content"],
                content_type=r["content_type"],
                source_type=r["source_type"],
                source_id=r["source_id"],
                agent_type=r["agent_type"],
                tags=r["tags"],
                metadata=r["metadata"],
                token_count=r["token_count"],
                relevance_score=r["relevance_score"],
                created_at=r["created_at"],
            )
            for r in results
        ]

    except Exception as e:
        logger.error(f"Failed to suggest projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_knowledge_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get knowledge base statistics.

    Returns counts by content type, agent type, and total entries.
    """
    try:
        from sqlalchemy import select, func
        from app.models.knowledge import KnowledgeEntry

        # Total entries
        total_result = await db.execute(select(func.count(KnowledgeEntry.id)))
        total = total_result.scalar()

        # By content type
        content_type_result = await db.execute(
            select(
                KnowledgeEntry.content_type,
                func.count(KnowledgeEntry.id).label("count"),
            ).group_by(KnowledgeEntry.content_type)
        )
        by_content_type = {row[0]: row[1] for row in content_type_result}

        # By agent type
        agent_type_result = await db.execute(
            select(
                KnowledgeEntry.agent_type,
                func.count(KnowledgeEntry.id).label("count"),
            )
            .where(KnowledgeEntry.agent_type.isnot(None))
            .group_by(KnowledgeEntry.agent_type)
        )
        by_agent_type = {row[0]: row[1] for row in agent_type_result}

        # Total tokens
        token_result = await db.execute(
            select(func.sum(KnowledgeEntry.token_count))
        )
        total_tokens = token_result.scalar() or 0

        return {
            "total_entries": total,
            "by_content_type": by_content_type,
            "by_agent_type": by_agent_type,
            "total_tokens": total_tokens,
        }

    except Exception as e:
        logger.error(f"Failed to get knowledge stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
