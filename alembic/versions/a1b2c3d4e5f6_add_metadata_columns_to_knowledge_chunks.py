"""add metadata columns to knowledge_chunks

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-09-28 15:50:40.028000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add project_name and company_name columns to knowledge_chunks for metadata pre-filtering."""

    # Add new metadata columns (nullable to allow existing rows)
    op.add_column('knowledge_chunks', sa.Column('project_name', sa.String(), nullable=True))
    op.add_column('knowledge_chunks', sa.Column('company_name', sa.String(), nullable=True))

    # Create indexes for faster filtering queries
    op.create_index('ix_knowledge_chunks_project_name', 'knowledge_chunks', ['project_name'])
    op.create_index('ix_knowledge_chunks_company_name', 'knowledge_chunks', ['company_name'])

    # Create composite index for common query patterns
    op.create_index('ix_knowledge_chunks_metadata', 'knowledge_chunks',
                    ['source_type', 'project_name', 'company_name'])


def downgrade() -> None:
    """Remove metadata columns and indexes."""

    # Drop indexes first
    op.drop_index('ix_knowledge_chunks_metadata', table_name='knowledge_chunks')
    op.drop_index('ix_knowledge_chunks_company_name', table_name='knowledge_chunks')
    op.drop_index('ix_knowledge_chunks_project_name', table_name='knowledge_chunks')

    # Drop columns
    op.drop_column('knowledge_chunks', 'company_name')
    op.drop_column('knowledge_chunks', 'project_name')
