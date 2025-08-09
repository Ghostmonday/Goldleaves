"""
Usage event model for tracking API usage with feature, jurisdiction, plan, and ai tags.
"""

from __future__ import annotations
from sqlalchemy import Column, String, Boolean, Text, JSON, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4
from typing import Optional, Dict, Any

from .dependencies import Base


class UsageEvent(Base):
    """Model for tracking usage events with tags."""
    
    __tablename__ = "usage_events"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier for the usage event"
    )
    
    # Required tags with defaults
    feature = Column(
        String(255),
        nullable=False,
        default="unknown",
        index=True,
        comment="Feature being used"
    )
    
    jurisdiction = Column(
        String(255),
        nullable=False,
        default="unknown",
        index=True,
        comment="Jurisdiction context"
    )
    
    plan = Column(
        String(255),
        nullable=False,
        default="unknown",
        index=True,
        comment="Plan context"
    )
    
    ai = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="AI feature usage flag"
    )
    
    # Additional event data
    event_type = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Type of usage event"
    )
    
    user_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="User associated with the event"
    )
    
    request_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Request ID for correlation"
    )
    
    metadata = Column(
        JSON,
        nullable=True,
        comment="Additional event metadata"
    )
    
    # Timestamp fields (manually added to avoid mixin complexity)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last update timestamp"
    )
    
    def __init__(
        self,
        feature: str = "unknown",
        jurisdiction: str = "unknown", 
        plan: str = "unknown",
        ai: bool = False,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize usage event with defaults."""
        super().__init__(**kwargs)
        self.feature = feature
        self.jurisdiction = jurisdiction
        self.plan = plan
        self.ai = ai
        self.event_type = event_type
        self.user_id = user_id
        self.request_id = request_id
        self.metadata = metadata or {}
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<UsageEvent(id={self.id}, feature={self.feature}, "
            f"jurisdiction={self.jurisdiction}, plan={self.plan}, ai={self.ai})>"
        )
    
    __table_args__ = (
        # Index for common query patterns
        {"comment": "Usage events for tracking API usage with feature tagging"}
    )