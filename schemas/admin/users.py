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
Admin user management schemas.
Provides schemas for administrative user operations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class AdminUserStatus(str, Enum):
    """Admin user status options."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    PENDING = "pending"
    DELETED = "deleted"


class AdminUserRole(str, Enum):
    """Admin user role options."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"


class AdminUserFilter(BaseModel):
    """Filter criteria for admin user queries."""
    
    status: Optional[AdminUserStatus] = Field(
        default=None,
        title="Status", description="Filter by user status"
    )
    
    role: Optional[AdminUserRole] = Field(
        default=None,
        title="Role", description="Filter by user role"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        title="Organization ID", description="Filter by organization"
    )
    
    email_domain: Optional[str] = Field(
        default=None,
        title="Email Domain", description="Filter by email domain"
    )
    
    created_after: Optional[datetime] = Field(
        default=None,
        title="Created After", description="Filter users created after this date"
    )
    
    created_before: Optional[datetime] = Field(
        default=None,
        title="Created Before", description="Filter users created before this date"
    )
    
    search: Optional[str] = Field(
        default=None,
        title="Search", description="Search in user details"
    )


class AdminUserUpdate(BaseModel):
    """Schema for admin user updates."""
    
    email: Optional[EmailStr] = Field(
        default=None,
        title="Email", description="User email address"
    )
    
    first_name: Optional[str] = Field(
        default=None,
        title="First Name", description="User first name"
    )
    
    last_name: Optional[str] = Field(
        default=None,
        title="Last Name", description="User last name"
    )
    
    status: Optional[AdminUserStatus] = Field(
        default=None,
        title="Status", description="User status"
    )
    
    role: Optional[AdminUserRole] = Field(
        default=None,
        title="Role", description="User role"
    )
    
    is_verified: Optional[bool] = Field(
        default=None,
        title="Is Verified", description="Email verification status"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Metadata", description="Additional user metadata"
    )


class AdminUserResponse(BaseModel):
    """Admin user response schema."""
    
    id: UUID = Field(
        title="User ID", description="Unique user identifier"
    )
    
    email: EmailStr = Field(
        title="Email", description="User email address"
    )
    
    first_name: str = Field(
        title="First Name", description="User first name"
    )
    
    last_name: str = Field(
        title="Last Name", description="User last name"
    )
    
    status: AdminUserStatus = Field(
        title="Status", description="User status"
    )
    
    role: AdminUserRole = Field(
        title="Role", description="User role"
    )
    
    is_verified: bool = Field(
        title="Is Verified", description="Email verification status"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        title="Organization ID", description="Primary organization"
    )
    
    last_login: Optional[datetime] = Field(
        default=None,
        title="Last Login", description="Last login timestamp"
    )
    
    login_count: int = Field(
        default=0,
        title="Login Count", description="Total login count"
    )
    
    created_at: datetime = Field(
        title="Created At", description="Account creation timestamp"
    )
    
    updated_at: datetime = Field(
        title="Updated At", description="Last update timestamp"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Metadata", description="Additional user metadata"
    )


class AdminUserAction(BaseModel):
    """Schema for admin user actions."""
    
    action: str = Field(
        title="Action", description="Action to perform"
    )
    
    reason: Optional[str] = Field(
        default=None,
        title="Reason", description="Reason for the action"
    )
    
    duration_days: Optional[int] = Field(
        default=None,
        title="Duration Days", description="Duration for temporary actions"
    )
    
    notify_user: bool = Field(
        default=True,
        title="Notify User", description="Whether to notify the user"
    )
    
    @validator('action')
    def validate_action(cls, v):
        """Validate action type."""
        allowed_actions = [
            'suspend', 'unsuspend', 'ban', 'unban', 
            'verify', 'unverify', 'reset_password',
            'force_logout', 'delete'
        ]
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v
