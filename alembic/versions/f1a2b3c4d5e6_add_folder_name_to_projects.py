"""add folder_name to projects

Revision ID: f1a2b3c4d5e6
Revises: 8d72e996b1e9
Create Date: 2026-09-10 15:55:41.397000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = '8d72e996b1e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add folder_name column to projects table and backfill existing data."""

    # Add folder_name column (nullable initially for backfill)
    op.add_column('projects', sa.Column('folder_name', sa.Text(), nullable=True))

    # Backfill existing 4 projects with their folder names
    op.execute("""
        UPDATE projects
        SET folder_name = 'kyc-onboarding'
        WHERE name = 'Automated KYC Onboarding System (Egyptian National ID)'
    """)

    op.execute("""
        UPDATE projects
        SET folder_name = 'agentic-rag-retail'
        WHERE name = 'Agentic RAG Retail Analytics'
    """)

    op.execute("""
        UPDATE projects
        SET folder_name = 'social-media-publishing'
        WHERE name = 'Social Campaign Publisher'
    """)

    op.execute("""
        UPDATE projects
        SET folder_name = 'pulsefit'
        WHERE name = 'PulseFit — AI-Powered Personal Trainer'
    """)

    # Now make it NOT NULL and UNIQUE (after backfill)
    op.alter_column('projects', 'folder_name', nullable=False)
    op.create_unique_constraint('uq_projects_folder_name', 'projects', ['folder_name'])


def downgrade() -> None:
    """Remove folder_name column from projects table."""
    op.drop_constraint('uq_projects_folder_name', 'projects', type_='unique')
    op.drop_column('projects', 'folder_name')
