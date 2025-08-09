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
Webhook configuration schemas for managing webhook endpoints and settings.
Provides schemas for creating, updating, and managing webhooks.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from ..dependencies import validate_url


class WebhookEvent(str, Enum):
    """Available webhook events."""
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    TEAM_CREATED = "team.created"
    MEMBER_ADDED = "member.added"
    MEMBER_REMOVED = "member.removed"


class WebhookStatus(str, Enum):
    """Webhook status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    SUSPENDED = "suspended"


class WebhookCreate(BaseModel):
    """Schema for creating a webhook."""
    
    name: str = Field(
        min_length=1, max_length=100,
        title="Webhook Name", description="Human-readable name for the webhook", example="User Registration Webhook"
    )
    
    url: str = Field(
        title="Webhook URL", description="Target URL for webhook delivery", example="https://api.example.com/webhooks/users"
    )
    
    events: List[WebhookEvent] = Field(
        min_items=1,
        title="Events", description="List of events that trigger this webhook"
    )
    
    secret: Optional[str] = Field(
        default=None,
        title="Secret", description="Optional secret for webhook signature verification"
    )
    
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        title="Custom Headers", description="Additional headers to include in webhook requests"
    )
    
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=120,
        title="Timeout", description="Request timeout in seconds (1-120)"
    )
    
    retry_count: int = Field(
        default=3,
        ge=0,
        le=10,
        title="Retry Count", description="Number of retry attempts on failure (0-10)"
    )
    
    @validator('url')
    def validate_webhook_url(cls, v):
        """Validate webhook URL format."""
        return validate_url(v)


class WebhookResponse(BaseModel):
    """Schema for webhook response."""
    
    id: UUID = Field(
        description="Unique webhook identifier"
    )
    
    organization_id: UUID = Field(
        description="Organization ID"
    )
    
    name: str = Field(
        title="Name", description="Webhook name"
    )
    
    url: str = Field(
        title="URL", description="Webhook target URL"
    )
    
    events: List[WebhookEvent] = Field(
        title="Events", description="Subscribed events"
    )
    
    status: WebhookStatus = Field(
        title="Status", description="Current webhook status"
    )
    
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        title="Headers", description="Custom headers"
    )
    
    timeout_seconds: int = Field(
        title="Timeout", description="Request timeout in seconds"
    )
    
    retry_count: int = Field(
        title="Retry Count", description="Retry attempts on failure"
    )
    
    last_triggered_at: Optional[datetime] = Field(
        default=None,
        description="Last time webhook was triggered"
    )
    
    success_count: int = Field(
        default=0,
        title="Success Count", description="Number of successful deliveries"
    )
    
    failure_count: int = Field(
        default=0,
        title="Failure Count", description="Number of failed deliveries"
    )
    
    created_at: datetime = Field(
        description="When webhook was created"
    )
    
    created_by: UUID = Field(
        description="User who created the webhook"
    )


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=1, max_length=100
    )
    
    url: Optional[str] = Field(
        default=None
    )
    
    events: Optional[List[WebhookEvent]] = Field(
        default=None,
        min_items=1
    )
    
    status: Optional[WebhookStatus] = Field(
        default=None
    )
    
    headers: Optional[Dict[str, str]] = Field(
        default=None
    )
    
    timeout_seconds: Optional[int] = Field(
        default=None,
        ge=1,
        le=120
    )
    
    retry_count: Optional[int] = Field(
        default=None,
        ge=0,
        le=10
    )
    
    @validator('url')
    def validate_webhook_url(cls, v):
        if v is not None:
            return validate_url(v)
        return v
