"""Add entitlements table

Revision ID: 202501010000
Revises: 776065168218
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '202501010000'
down_revision = '776065168218'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create entitlements table
    op.create_table(
        'entitlements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('plan', sa.Enum('FREE', 'PRO', 'TEAM', name='plantype'), nullable=False),
        sa.Column('seats', sa.Integer(), nullable=False),
        sa.Column('features', sa.JSON(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        
        # Base model columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.String(length=255), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Check constraints
        sa.CheckConstraint('(user_id IS NULL) != (tenant_id IS NULL)', name='check_user_or_tenant_not_both'),
        sa.CheckConstraint('seats > 0', name='check_seats_positive'),
        
        # Unique constraints
        sa.UniqueConstraint('user_id', 'tenant_id', name='uq_entitlement_user_tenant')
    )
    
    # Create indexes for performance
    op.create_index('idx_entitlement_user_active', 'entitlements', ['user_id', 'active'])
    op.create_index('idx_entitlement_tenant_active', 'entitlements', ['tenant_id', 'active'])
    op.create_index('idx_entitlement_plan_active', 'entitlements', ['plan', 'active'])
    op.create_index('idx_entitlement_stripe_customer', 'entitlements', ['stripe_customer_id'])
    op.create_index('idx_entitlement_stripe_subscription', 'entitlements', ['stripe_subscription_id'])
    op.create_index(op.f('ix_entitlements_id'), 'entitlements', ['id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_entitlements_id'), table_name='entitlements')
    op.drop_index('idx_entitlement_stripe_subscription', table_name='entitlements')
    op.drop_index('idx_entitlement_stripe_customer', table_name='entitlements')
    op.drop_index('idx_entitlement_plan_active', table_name='entitlements')
    op.drop_index('idx_entitlement_tenant_active', table_name='entitlements')
    op.drop_index('idx_entitlement_user_active', table_name='entitlements')
    
    # Drop table
    op.drop_table('entitlements')
    
    # Drop enum type
    op.execute('DROP TYPE plantype')