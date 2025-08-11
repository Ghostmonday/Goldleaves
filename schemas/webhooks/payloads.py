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
Webhook payload schemas for different event types.
Provides standardized payload structures for webhook events.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID



class WebhookPayload(BaseModel):
    """Base webhook payload structure."""
    
    event: str = Field(
        title="Event", description="Event type that triggered the webhook"
    )
    
    timestamp: datetime = Field(
        description="When the event occurred"
    )
    
    organization_id: UUID = Field(
        description="Organization where event occurred"
    )
    
    data: Dict[str, Any] = Field(
        title="Event Data", description="Event-specific data payload"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Metadata", description="Additional context and metadata"
    )


class UserWebhookPayload(WebhookPayload):
    """Webhook payload for user events."""
    
    user_id: UUID = Field(
        description="User ID involved in the event"
    )


class DocumentWebhookPayload(WebhookPayload):
    """Webhook payload for document events."""
    
    document_id: UUID = Field(
        description="Document ID involved in the event"
    )
    
    user_id: UUID = Field(
        description="User who triggered the event"
    )


class OrganizationWebhookPayload(WebhookPayload):
    """Webhook payload for organization events."""
    
    user_id: UUID = Field(
        description="User who triggered the event"
    )
