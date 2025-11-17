"""Initial schema with all tables

Revision ID: 001
Revises:
Create Date: 2025-11-17 18:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=True),
        sa.Column('credits_balance', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('language_code', sa.String(length=10), nullable=True),
        sa.Column('is_premium', sa.Boolean(), nullable=True),
        sa.Column('credits_balance', sa.Integer(), nullable=True),
        sa.Column('last_active_at', sa.DateTime(), nullable=False),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)

    # Create user_settings table
    op.create_table('user_settings',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('theme', sa.String(length=20), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=True),
        sa.Column('auto_execute', sa.Boolean(), nullable=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('user_id')
    )

    # Create projects table
    op.create_table('projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'PLANNING', 'IN_PROGRESS', 'REVIEW', 'COMPLETED', 'CANCELLED', name='projectstatus'), nullable=False),
        sa.Column('type', sa.Enum('WEBSITE', 'MOBILE_APP', 'MARKETING_CAMPAIGN', 'DATA_ANALYSIS', 'CONTENT_CREATION', 'CUSTOM', name='projecttype'), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'], unique=False)

    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('action_url', sa.String(length=500), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    # Create tasks table
    op.create_table('tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assigned_agent', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'REVIEW', 'COMPLETED', 'FAILED', 'BLOCKED', name='taskstatus'), nullable=False),
        sa.Column('priority', sa.Enum('CRITICAL', 'HIGH', 'NORMAL', 'LOW', name='taskpriority'), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=True),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('dependencies', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('estimated_tokens', sa.Integer(), nullable=True),
        sa.Column('actual_tokens', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_project_id'), 'tasks', ['project_id'], unique=False)

    # Create agent_executions table
    op.create_table('agent_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', sa.String(length=100), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_executions_task_id'), 'agent_executions', ['task_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_agent_executions_task_id'), table_name='agent_executions')
    op.drop_table('agent_executions')

    op.drop_index(op.f('ix_tasks_project_id'), table_name='tasks')
    op.drop_table('tasks')

    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_table('notifications')

    op.drop_index(op.f('ix_projects_user_id'), table_name='projects')
    op.drop_table('projects')

    op.drop_table('user_settings')

    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_table('users')

    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_table('organizations')

    # Drop enums
    sa.Enum(name='taskpriority').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='taskstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='projecttype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='projectstatus').drop(op.get_bind(), checkfirst=True)
