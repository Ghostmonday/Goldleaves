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
Audit logs schemas.
Provides schemas for audit trail and logging functionality.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from uuid import UUID



class AuditAction(str, Enum):
    """Audit action types."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    SHARE = "share"
    UNSHARE = "unshare"


class AuditLevel(str, Enum):
    """Audit log levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogEntry(BaseModel):
    """Audit log entry schema."""
    
    id: Optional[UUID] = Field(
        default=None,
        title="Log Entry ID", description="Unique identifier for the audit log entry"
    )
    
    user_id: Optional[UUID] = Field(
        default=None,
        title="User ID", description="ID of the user who performed the action"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        title="Organization ID", description="ID of the organization context"
    )
    
    action: AuditAction = Field(
        title="Action", description="Type of action performed"
    )
    
    resource_type: str = Field(
        title="Resource Type", description="Type of resource affected"
    )
    
    resource_id: Optional[str] = Field(
        default=None,
        title="Resource ID", description="ID of the affected resource"
    )
    
    level: AuditLevel = Field(
        default=AuditLevel.INFO,
        title="Log Level", description="Severity level of the audit entry"
    )
    
    message: str = Field(
        title="Message", description="Human-readable description of the action"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Metadata", description="Additional context data"
    )
    
    ip_address: Optional[str] = Field(
        default=None,
        title="IP Address", description="IP address of the client"
    )
    
    user_agent: Optional[str] = Field(
        default=None,
        title="User Agent", description="Browser/client user agent"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        title="Timestamp", description="When the action occurred"
    )


class AuditFilter(BaseModel):
    """Audit log filter criteria."""
    
    user_id: Optional[UUID] = Field(
        default=None,
        title="User ID", description="Filter by user ID"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        title="Organization ID", description="Filter by organization ID"
    )
    
    actions: Optional[List[AuditAction]] = Field(
        default=None,
        title="Actions", description="Filter by action types"
    )
    
    resource_type: Optional[str] = Field(
        default=None,
        title="Resource Type", description="Filter by resource type"
    )
    
    resource_id: Optional[str] = Field(
        default=None,
        title="Resource ID", description="Filter by resource ID"
    )
    
    level: Optional[AuditLevel] = Field(
        default=None,
        title="Log Level", description="Filter by log level"
    )
    
    from_date: Optional[datetime] = Field(
        default=None,
        title="From Date", description="Filter logs from this date"
    )
    
    to_date: Optional[datetime] = Field(
        default=None,
        title="To Date", description="Filter logs until this date"
    )
    
    search: Optional[str] = Field(
        default=None,
        title="Search", description="Search in log messages"
    )
    
    @validator('to_date')
    def validate_date_range(cls, v, values):
        """Validate date range."""
        if v and 'from_date' in values and values['from_date']:
            if v < values['from_date']:
                raise ValueError('to_date must be after from_date')
        return v


class AuditLogCreate(BaseModel):
    """Schema for creating audit log entries."""
    
    user_id: Optional[UUID] = Field(
        default=None,
        title="User ID", description="ID of the user performing the action"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        title="Organization ID", description="Organization context"
    )
    
    action: AuditAction = Field(
        title="Action", description="Action being performed"
    )
    
    resource_type: str = Field(
        title="Resource Type", description="Type of resource being affected"
    )
    
    resource_id: Optional[str] = Field(
        default=None,
        title="Resource ID", description="ID of the affected resource"
    )
    
    level: AuditLevel = Field(
        default=AuditLevel.INFO,
        title="Log Level", description="Severity level"
    )
    
    message: str = Field(
        title="Message", description="Description of the action"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Metadata", description="Additional context data"
    )
    
    ip_address: Optional[str] = Field(
        default=None,
        title="IP Address", description="Client IP address"
    )
    
    user_agent: Optional[str] = Field(
        default=None,
        title="User Agent", description="Client user agent"
    )
