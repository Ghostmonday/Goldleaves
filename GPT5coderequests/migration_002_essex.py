# alembic/versions/002_add_org_and_billing_events.py
"""Add organizations and billing_events tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'  # Set to the actual prior revision id in this repo
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create billing_events table
    op.create_table('billing_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=40), nullable=True),
        sa.Column('event_name', sa.String(length=64), nullable=True),
        sa.Column('resource_id', sa.String(length=64), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=12, scale=4), server_default='1.0', nullable=True),
        sa.Column('unit', sa.String(length=16), server_default='call', nullable=True),
        sa.Column('unit_cost_cents', sa.Integer(), nullable=True),
        sa.Column('dimensions', sa.JSON(), nullable=True),
        sa.Column('status', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_billing_events_organization_id'), 'billing_events', ['organization_id'], unique=False)
    op.create_index(op.f('ix_billing_events_event_name'), 'billing_events', ['event_name'], unique=False)
    op.create_index('ix_billing_events_org_created', 'billing_events', ['organization_id', 'created_at'], unique=False)
    
    # Optionally create organizations table if it doesn't exist
    # (commented out - add if needed)
    # op.create_table('organizations',
    #     sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    #     sa.Column('name', sa.String(length=255), nullable=False),
    #     sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    #     sa.PrimaryKeyConstraint('id')
    # )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_billing_events_org_created', table_name='billing_events')
    op.drop_index(op.f('ix_billing_events_event_name'), table_name='billing_events')
    op.drop_index(op.f('ix_billing_events_organization_id'), table_name='billing_events')
    
    # Drop table
    op.drop_table('billing_events')
    
    # If organizations table was created, drop it
    # op.drop_table('organizations')