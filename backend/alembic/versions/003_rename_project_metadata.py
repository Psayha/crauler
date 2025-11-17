"""Rename metadata to project_metadata in projects table

Revision ID: 003_rename_project_metadata
Revises: 002_add_hr_agent_tables
Create Date: 2025-11-17

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '003_rename_project_metadata'
down_revision = '002_add_hr_agent_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename metadata column to project_metadata (metadata is reserved by SQLAlchemy)."""
    op.alter_column('projects', 'metadata', new_column_name='project_metadata')


def downgrade() -> None:
    """Rename project_metadata back to metadata."""
    op.alter_column('projects', 'project_metadata', new_column_name='metadata')
