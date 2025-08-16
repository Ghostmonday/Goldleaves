"""Add entitlements table for billing

Revision ID: 001_add_entitlements
Revises:
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_entitlements'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create entitlements table."""
    # Create enum type for plan
    plan_enum = postgresql.ENUM('free', 'pro', 'team', name='plantype')
    plan_enum.create(op.get_bind())

    # Create entitlements table
    op.create_table(
        'entitlements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=True),
        sa.Column('subscription_id', sa.String(), nullable=True),
        sa.Column('plan', plan_enum, nullable=False, server_default='free'),
        sa.Column('cycle_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cycle_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_entitlement_tenant', 'entitlements', ['tenant_id'])
    op.create_index('idx_entitlement_customer', 'entitlements', ['customer_id'])
    op.create_index('idx_entitlement_subscription', 'entitlements', ['subscription_id'])
    op.create_index('idx_entitlement_plan', 'entitlements', ['plan'])


def downgrade():
    """Drop entitlements table."""
    # Drop indexes
    op.drop_index('idx_entitlement_plan', table_name='entitlements')
    op.drop_index('idx_entitlement_subscription', table_name='entitlements')
    op.drop_index('idx_entitlement_customer', table_name='entitlements')
    op.drop_index('idx_entitlement_tenant', table_name='entitlements')

    # Drop table
    op.drop_table('entitlements')

    # Drop enum type
    plan_enum = postgresql.ENUM('free', 'pro', 'team', name='plantype')
    plan_enum.drop(op.get_bind())
