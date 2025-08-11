# === AGENT CONTEXT: SCHEMAS AGENT ===
# 🚧 TODOs for Phase 4 — Complete schema contracts
# - [x] Define all Pydantic schemas with type-safe fields
# - [x] Add pagination, response, and error wrapper patterns
# - [x] Validate alignment with models/ and services/ usage
# - [x] Enforce exports via `schemas/contract.py`
# - [x] Ensure each schema has at least one integration test
# - [x] Maintain strict folder isolation (no model/service imports)
# - [x] Add version string and export mapping to `SchemaContract`
# - [x] Annotate fields with metadata for future auto-docs

"""
Audit events schemas.
Provides schemas for system events and activity tracking.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from uuid import UUID



class EventType(str, Enum):
    """System event types."""
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_SHARED = "document.shared"
    DOCUMENT_UNSHARED = "document.unshared"
    
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_DELETED = "organization.deleted"
    
    TEAM_CREATED = "team.created"
    TEAM_UPDATED = "team.updated"
    TEAM_DELETED = "team.deleted"
    
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_REVOKED = "permission.revoked"
    
    SECURITY_BREACH = "security.breach"
    SECURITY_WARNING = "security.warning"


class EventSeverity(str, Enum):
    """Event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """Audit event schema."""
    
    id: Optional[UUID] = Field(
        default=None,
        title="Event ID", description="Unique identifier for the event"
    )
    
    event_type: EventType = Field(
        title="Event Type", description="Type of event that occurred"
    )
    
    severity: EventSeverity = Field(
        default=EventSeverity.LOW,
        title="Severity", description="Severity level of the event"
    )
    
    actor_id: Optional[UUID] = Field(
        default=None,
        title="Actor ID", description="ID of the user/system that triggered the event"
    )
    
    actor_type: str = Field(
        default="user",
        title="Actor Type", description="Type of actor (user, system, service)"
    )
    
    target_id: Optional[UUID] = Field(
        default=None,
        title="Target ID", description="ID of the target resource"
    )
    
    target_type: str = Field(
        title="Target Type", description="Type of target resource"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        title="Organization ID", description="Organization context for the event"
    )
    
    summary: str = Field(
        title="Summary", description="Brief description of the event"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Details", description="Detailed event information"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Metadata", description="Additional event metadata"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        title="Timestamp", description="When the event occurred"
    )
    
    correlation_id: Optional[str] = Field(
        default=None,
        title="Correlation ID", description="ID to correlate related events"
    )


class EventFilter(BaseModel):
    """Event filter criteria."""
    
    event_types: Optional[List[EventType]] = Field(
        default=None,
        title="Event Types", description="Filter by event types"
    )
    
    severity: Optional[EventSeverity] = Field(
        default=None,
        title="Severity", description="Filter by severity level"
    )
    
    actor_id: Optional[UUID] = Field(
        default=None,
        title="Actor ID", description="Filter by actor ID"
    )
    
    target_id: Optional[UUID] = Field(
        default=None,
        title="Target ID", description="Filter by target ID"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        title="Organization ID", description="Filter by organization"
    )
    
    from_date: Optional[datetime] = Field(
        default=None,
        title="From Date", description="Filter events from this date"
    )
    
    to_date: Optional[datetime] = Field(
        default=None,
        title="To Date", description="Filter events until this date"
    )
    
    correlation_id: Optional[str] = Field(
        default=None,
        title="Correlation ID", description="Filter by correlation ID"
    )


class EventCreate(BaseModel):
    """Schema for creating audit events."""
    
    event_type: EventType = Field(
        title="Event Type", description="Type of event"
    )
    
    severity: EventSeverity = Field(
        default=EventSeverity.LOW,
        title="Severity", description="Event severity"
    )
    
    actor_id: Optional[UUID] = Field(
        default=None,
        title="Actor ID", description="ID of the actor"
    )
    
    actor_type: str = Field(
        default="user",
        title="Actor Type", description="Type of actor"
    )
    
    target_id: Optional[UUID] = Field(
        default=None,
        title="Target ID", description="ID of the target"
    )
    
    target_type: str = Field(
        title="Target Type", description="Type of target"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        title="Organization ID", description="Organization context"
    )
    
    summary: str = Field(
        title="Summary", description="Event summary"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Details", description="Event details"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Metadata", description="Event metadata"
    )
    
    correlation_id: Optional[str] = Field(
        default=None,
        title="Correlation ID", description="Correlation identifier"
    )
