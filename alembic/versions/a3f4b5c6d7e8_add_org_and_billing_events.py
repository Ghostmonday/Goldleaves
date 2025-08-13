"""Add organizations and billing_events tables

Revision ID: a3f4b5c6d7e8
Revises: 202501010000
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a3f4b5c6d7e8"
# IMPORTANT: set this to your actual previous migration
down_revision = "202501010000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgcrypto for gen_random_uuid
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    except Exception:
        # Ignore on non-Postgres backends
        pass

    # Create organizations table
    op.create_table(
        "organizations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=True),
        sa.Column("plan", sa.String(length=50), server_default="starter", nullable=True),
        sa.Column(
            "settings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    # Create billing_events table with UUID and JSONB
    op.create_table(
        "billing_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=True),
        sa.Column("event_name", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column(
            "quantity",
            sa.Numeric(precision=12, scale=4),
            server_default="1.0",
            nullable=True,
        ),
        sa.Column("unit", sa.String(length=16), server_default="call", nullable=True),
        sa.Column("unit_cost_cents", sa.Integer(), nullable=True),
        sa.Column(
            "dimensions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column("status", sa.Integer(), server_default="0", nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_billing_events_organization_id"),
        "billing_events",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_billing_events_event_name"),
        "billing_events",
        ["event_name"],
        unique=False,
    )
    op.create_index(
        "ix_billing_events_org_created",
        "billing_events",
        ["organization_id", "created_at"],
        unique=False,
    )

    # Create GIN index for JSONB dimensions
    try:
        op.create_index(
            "ix_billing_events_dimensions",
            "billing_events",
            ["dimensions"],
            unique=False,
            postgresql_using="gin",
        )
    except Exception:
        # Ignore on non-Postgres backends
        pass


def downgrade() -> None:
    # Drop indexes and tables in reverse order
    try:
        op.drop_index("ix_billing_events_dimensions", table_name="billing_events")
    except Exception:
        pass
    op.drop_index("ix_billing_events_org_created", table_name="billing_events")
    op.drop_index(op.f("ix_billing_events_event_name"), table_name="billing_events")
    op.drop_index(op.f("ix_billing_events_organization_id"), table_name="billing_events")
    op.drop_table("billing_events")

    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
