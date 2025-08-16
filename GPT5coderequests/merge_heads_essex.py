# alembic/versions/merge_heads_12345.py
"""Merge multiple heads into one

Revision ID: merge_heads_12345
Revises: 002, other_head
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_heads_12345'
down_revision = ('002', 'other_head')  # List all heads to merge
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a merge migration, no schema changes needed
    pass


def downgrade() -> None:
    # This is a merge migration, no schema changes needed
    pass