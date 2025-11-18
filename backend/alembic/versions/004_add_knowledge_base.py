"""Add Knowledge Base tables with pgvector

Revision ID: 004
Revises: 003_rename_project_metadata
Create Date: 2025-11-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003_rename_project_metadata'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create knowledge_entries table
    op.create_table('knowledge_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=True),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),  # Will be vector(1536)
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_type', sa.String(length=100), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('knowledge_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_knowledge_entries_title'), 'knowledge_entries', ['title'], unique=False)
    op.create_index(op.f('ix_knowledge_entries_source_id'), 'knowledge_entries', ['source_id'], unique=False)
    op.create_index(op.f('ix_knowledge_entries_agent_type'), 'knowledge_entries', ['agent_type'], unique=False)

    # Convert embedding column to vector type
    # Note: Using raw SQL because pgvector types aren't directly supported in Alembic column definitions
    op.execute('ALTER TABLE knowledge_entries ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)')

    # Create vector index for similarity search (using HNSW for fast approximate search)
    op.execute('CREATE INDEX knowledge_entries_embedding_idx ON knowledge_entries USING hnsw (embedding vector_cosine_ops)')

    # Create search_queries table
    op.create_table('search_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=True),
        sa.Column('top_result_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('search_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for search_queries
    op.create_index(op.f('ix_search_queries_user_id'), 'search_queries', ['user_id'], unique=False)
    op.create_index(op.f('ix_search_queries_project_id'), 'search_queries', ['project_id'], unique=False)

    # Convert query_embedding column to vector type
    op.execute('ALTER TABLE search_queries ALTER COLUMN query_embedding TYPE vector(1536) USING query_embedding::vector(1536)')


def downgrade() -> None:
    # Drop search_queries table and indexes
    op.drop_index(op.f('ix_search_queries_project_id'), table_name='search_queries')
    op.drop_index(op.f('ix_search_queries_user_id'), table_name='search_queries')
    op.drop_table('search_queries')

    # Drop knowledge_entries indexes and table
    op.execute('DROP INDEX IF EXISTS knowledge_entries_embedding_idx')
    op.drop_index(op.f('ix_knowledge_entries_agent_type'), table_name='knowledge_entries')
    op.drop_index(op.f('ix_knowledge_entries_source_id'), table_name='knowledge_entries')
    op.drop_index(op.f('ix_knowledge_entries_title'), table_name='knowledge_entries')
    op.drop_table('knowledge_entries')

    # Note: We don't drop the vector extension as other tables might use it
    # op.execute('DROP EXTENSION IF EXISTS vector')
