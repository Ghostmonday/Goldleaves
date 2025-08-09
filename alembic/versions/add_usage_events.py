"""Add usage_events table for metered billing

Revision ID: add_usage_events
Revises: 
Create Date: 2024-08-09 12:18:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_usage_events'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add usage_events table for usage tracking and metered billing."""
    
    # Create usage_events table
    op.create_table('usage_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_id', sa.String(length=255), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('route', sa.String(length=500), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('units', sa.Float(), nullable=False),
        sa.Column('cost_cents', sa.Integer(), nullable=True),
        sa.Column('ts', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata', sa.String(length=2000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_id', name='uq_usage_request_id')
    )
    
    # Create performance indexes
    op.create_index('idx_usage_tenant_ts', 'usage_events', ['tenant_id', 'ts'])
    op.create_index('idx_usage_user_ts', 'usage_events', ['user_id', 'ts'])
    op.create_index('idx_usage_route_ts', 'usage_events', ['route', 'ts'])
    op.create_index('idx_usage_tenant_route', 'usage_events', ['tenant_id', 'route'])
    op.create_index('idx_usage_request_id', 'usage_events', ['request_id'])


def downgrade() -> None:
    """Remove usage_events table."""
    
    # Drop indexes first
    op.drop_index('idx_usage_request_id', table_name='usage_events')
    op.drop_index('idx_usage_tenant_route', table_name='usage_events')
    op.drop_index('idx_usage_route_ts', table_name='usage_events')
    op.drop_index('idx_usage_user_ts', table_name='usage_events')
    op.drop_index('idx_usage_tenant_ts', table_name='usage_events')
    
    # Drop table
    op.drop_table('usage_events')