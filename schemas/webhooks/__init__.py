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
Webhook schema module exports.
Provides schemas for webhook configuration and payloads.
"""

# Configuration schemas
from .config import (
    WebhookCreate,
    WebhookEvent,
    WebhookResponse,
    WebhookStatus,
    WebhookUpdate,
)

# Payload schemas
from .payloads import (
    DocumentWebhookPayload,
    OrganizationWebhookPayload,
    UserWebhookPayload,
    WebhookPayload,
)

__all__ = [
    # Configuration schemas
    "WebhookEvent",
    "WebhookStatus",
    "WebhookCreate",
    "WebhookResponse",
    "WebhookUpdate",

    # Payload schemas
    "WebhookPayload",
    "UserWebhookPayload",
    "DocumentWebhookPayload",
    "OrganizationWebhookPayload",
]
