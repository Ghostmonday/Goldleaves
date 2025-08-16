"""DEPRECATED: superseded by a3f4b5c6d7e8; kept as no-op to preserve history.

Revision ID: deprecated_002
Revises: a3f4b5c6d7e8
Create Date: 2025-08-12
"""
from __future__ import annotations

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "deprecated_002"
down_revision = "a3f4b5c6d7e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op; replaced by a3f4b5c6d7e8
    pass


def downgrade() -> None:
    # No-op
    pass
