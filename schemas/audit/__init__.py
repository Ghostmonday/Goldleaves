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
Audit module exports.
Centralized exports for audit-related schemas.
"""

from .logs import (
    AuditAction,
    AuditLevel,
    AuditLogEntry,
    AuditFilter,
    AuditLogCreate
)

from .events import (
    EventType,
    EventSeverity,
    AuditEvent,
    EventFilter,
    EventCreate
)

__all__ = [
    # Logs
    "AuditAction",
    "AuditLevel", 
    "AuditLogEntry",
    "AuditFilter",
    "AuditLogCreate",
    
    # Events
    "EventType",
    "EventSeverity",
    "AuditEvent", 
    "EventFilter",
    "EventCreate"
]
