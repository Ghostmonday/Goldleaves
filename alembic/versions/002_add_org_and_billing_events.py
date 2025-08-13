"""add org and billing events tables (PR-1)

Revision ID: 002
Revises:
Create Date: 2025-08-12
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002"
# Chain after the latest known migration in this repo
down_revision = "202501010000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # organizations table (minimal)
    if not op.get_bind().dialect.has_table(op.get_bind(), "organizations"):
        op.create_table(
            "organizations",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("slug", sa.String(255), nullable=True, index=True),
        )
    # Add organization_id to common tables if exist
    for tbl in ("users", "clients", "cases", "documents"):
        try:
            op.add_column(tbl, sa.Column("organization_id", sa.Integer, nullable=True))
        except Exception:
            pass

    # billing_events table
    op.create_table(
        "billing_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer, index=True),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("event_name", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(64)),
        sa.Column("quantity", sa.Numeric(12, 4), server_default="1.0", nullable=False),
        sa.Column("unit", sa.String(16), server_default="call", nullable=False),
        sa.Column("unit_cost_cents", sa.Integer),
        sa.Column("dimensions", sa.JSON),
        sa.Column("status", sa.Integer, server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_billing_events_org_created", "billing_events", ["organization_id", "created_at"])
    op.create_index("ix_billing_events_name", "billing_events", ["event_name"])


def downgrade() -> None:
    try:
        op.drop_index("ix_billing_events_name", table_name="billing_events")
        op.drop_index("ix_billing_events_org_created", table_name="billing_events")
        op.drop_table("billing_events")
    except Exception:
        pass
    for tbl in ("users", "clients", "cases", "documents"):
        try:
            op.drop_column(tbl, "organization_id")
        except Exception:
            pass
    try:
        op.drop_table("organizations")
    except Exception:
        pass
