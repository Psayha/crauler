"""Add HR Agent tables

Revision ID: 002
Revises: 001
Create Date: 2025-11-17 19:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agent_performance_metrics table
    op.create_table('agent_performance_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', sa.String(length=100), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_tasks', sa.Integer(), nullable=True),
        sa.Column('successful_tasks', sa.Integer(), nullable=True),
        sa.Column('failed_tasks', sa.Integer(), nullable=True),
        sa.Column('avg_execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('total_tokens_used', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_performance_metrics_agent_type'), 'agent_performance_metrics', ['agent_type'], unique=False)

    # Create agent_improvements table
    op.create_table('agent_improvements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', sa.String(length=100), nullable=False),
        sa.Column('improvement_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('previous_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('test_results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('performance_impact', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_improvements_agent_type'), 'agent_improvements', ['agent_type'], unique=False)

    # Create dynamic_agents table
    op.create_table('dynamic_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('expertise', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('capabilities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by_project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('creation_reason', sa.Text(), nullable=True),
        sa.Column('validation_score', sa.Float(), nullable=True),
        sa.Column('validation_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('avg_quality_score', sa.Float(), nullable=True),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('deprecated_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_type')
    )
    op.create_index(op.f('ix_dynamic_agents_agent_type'), 'dynamic_agents', ['agent_type'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_dynamic_agents_agent_type'), table_name='dynamic_agents')
    op.drop_table('dynamic_agents')

    op.drop_index(op.f('ix_agent_improvements_agent_type'), table_name='agent_improvements')
    op.drop_table('agent_improvements')

    op.drop_index(op.f('ix_agent_performance_metrics_agent_type'), table_name='agent_performance_metrics')
    op.drop_table('agent_performance_metrics')
