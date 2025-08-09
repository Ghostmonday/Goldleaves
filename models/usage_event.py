"""
Usage Event model for tracking billable requests and metered billing.
Records each billable API request with deduplication via request_id.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Integer, Float, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from .base import Base, TimestampMixin


class UsageEvent(Base, TimestampMixin):
    """Model for tracking billable usage events with idempotency."""
    
    __tablename__ = "usage_events"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier for the usage event"
    )
    
    # Request identification and context
    request_id = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique request identifier for idempotency"
    )
    
    tenant_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Tenant/organization identifier"
    )
    
    user_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="User identifier who made the request"
    )
    
    # API endpoint information
    route = Column(
        String(500),
        nullable=False,
        index=True,
        comment="API route/endpoint that was accessed"
    )
    
    action = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Action performed (e.g., create, read, update, delete)"
    )
    
    # Usage metrics
    units = Column(
        Float,
        nullable=False,
        default=1.0,
        comment="Number of units consumed (can be fractional)"
    )
    
    cost_cents = Column(
        Integer,
        nullable=True,
        comment="Cost in cents for this usage event"
    )
    
    # Timestamp (UTC)
    ts = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="UTC timestamp when the event occurred"
    )
    
    # Additional metadata
    metadata = Column(
        String(2000),
        nullable=True,
        comment="Additional metadata as JSON string"
    )
    
    # Performance indexes
    __table_args__ = (
        Index('idx_usage_tenant_ts', 'tenant_id', 'ts'),
        Index('idx_usage_user_ts', 'user_id', 'ts'),
        Index('idx_usage_route_ts', 'route', 'ts'),
        Index('idx_usage_tenant_route', 'tenant_id', 'route'),
        UniqueConstraint('request_id', name='uq_usage_request_id'),
    )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<UsageEvent(id={self.id}, request_id='{self.request_id}', "
            f"tenant='{self.tenant_id}', route='{self.route}', "
            f"units={self.units}, cost_cents={self.cost_cents})>"
        )
    
    def calculate_cost(self, rate_cents: int) -> int:
        """Calculate cost based on units and rate."""
        return int(self.units * rate_cents)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': str(self.id),
            'request_id': self.request_id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'route': self.route,
            'action': self.action,
            'units': self.units,
            'cost_cents': self.cost_cents,
            'ts': self.ts.isoformat() if self.ts else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def get_by_request_id(cls, db, request_id: str) -> Optional['UsageEvent']:
        """Get usage event by request ID for idempotency checks."""
        return db.query(cls).filter(cls.request_id == request_id).first()
    
    @classmethod
    def get_usage_for_tenant(
        cls, 
        db, 
        tenant_id: str, 
        start_date: datetime,
        end_date: datetime
    ) -> list['UsageEvent']:
        """Get usage events for a tenant within a date range."""
        return db.query(cls).filter(
            cls.tenant_id == tenant_id,
            cls.ts >= start_date,
            cls.ts <= end_date
        ).order_by(cls.ts.desc()).all()
    
    @classmethod
    def get_usage_summary(
        cls,
        db,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """Get usage summary for a tenant within a date range."""
        from sqlalchemy import func as sql_func
        
        result = db.query(
            sql_func.count(cls.id).label('total_events'),
            sql_func.sum(cls.units).label('total_units'),
            sql_func.sum(cls.cost_cents).label('total_cost_cents'),
            sql_func.count(sql_func.distinct(cls.route)).label('unique_routes')
        ).filter(
            cls.tenant_id == tenant_id,
            cls.ts >= start_date,
            cls.ts <= end_date
        ).first()
        
        return {
            'tenant_id': tenant_id,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_events': result.total_events or 0,
            'total_units': float(result.total_units or 0),
            'total_cost_cents': int(result.total_cost_cents or 0),
            'unique_routes': result.unique_routes or 0
        }