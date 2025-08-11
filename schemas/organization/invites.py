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
Organization invitation management schemas.
Provides schemas for inviting users to organizations and managing invitations.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID

from ..dependencies import (
    email_field,
    create_field_metadata
)


class InviteStatus(str, Enum):
    """Invitation status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class InviteType(str, Enum):
    """Type of invitation."""
    ORGANIZATION = "organization"
    TEAM = "team"
    DOCUMENT = "document"


class InviteCreate(BaseModel):
    """Schema for creating an invitation."""
    
    email: str = Field(
        **email_field(),
        title="Email", description="Email address to send invitation to", example="user@example.com"
    )
    
    role: str = Field(
        min_length=1, max_length=50,
        title="Role", description="Role to assign to the invited user", example="member"
    )
    
    team_ids: Optional[List[UUID]] = Field(
        default=None,
        title="Team IDs", description="Teams to add the user to upon acceptance"
    )
    
    message: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Custom Message", description="Custom message to include in the invitation"
    )
    
    expires_in_days: int = Field(
        default=7,
        ge=1,
        le=30,
        **create_field_metadata(
            title="Expires In Days",
            description="Number of days until invitation expires (1-30)",
            example=7
        )
    )
    
    permissions: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Permissions", description="Custom permissions to assign upon acceptance"
    )


class InviteUpdate(BaseModel):
    """Schema for updating an invitation."""
    
    message: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Custom Message", description="Updated custom message"
    )
    
    role: Optional[str] = Field(
        default=None,
        min_length=1, max_length=50,
        title="Role", description="Updated role assignment"
    )
    
    team_ids: Optional[List[UUID]] = Field(
        default=None,
        title="Team IDs", description="Updated team assignments"
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        title="Expires At", description="Updated expiration time"
    )


class InviteResponse(BaseModel):
    """Schema for invitation response."""
    
    id: UUID = Field(
        description="Unique invitation identifier"
    )
    
    organization_id: UUID = Field(
        description="Organization ID"
    )
    
    organization_name: str = Field(
        title="Organization Name", description="Name of the organization"
    )
    
    email: str = Field(
        title="Email", description="Email address of the invitee"
    )
    
    role: str = Field(
        title="Role", description="Role to be assigned"
    )
    
    status: InviteStatus = Field(
        title="Status", description="Current invitation status"
    )
    
    invite_type: InviteType = Field(
        default=InviteType.ORGANIZATION,
        title="Invite Type", description="Type of invitation"
    )
    
    team_ids: Optional[List[UUID]] = Field(
        default=None,
        title="Team IDs", description="Teams the user will be added to"
    )
    
    team_names: Optional[List[str]] = Field(
        default=None,
        title="Team Names", description="Names of teams the user will be added to"
    )
    
    message: Optional[str] = Field(
        title="Message", description="Custom invitation message"
    )
    
    token: Optional[str] = Field(
        default=None,
        title="Token", description="Invitation token (only shown to sender)"
    )
    
    invite_url: Optional[str] = Field(
        default=None,
        title="Invite URL", description="Complete invitation URL"
    )
    
    permissions: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Permissions", description="Permissions to be assigned"
    )
    
    invited_by: UUID = Field(
        description="User who sent the invitation"
    )
    
    invited_by_name: Optional[str] = Field(
        default=None,
        title="Invited By Name", description="Name of the user who sent the invitation"
    )
    
    created_at: datetime = Field(
        description="When the invitation was created"
    )
    
    expires_at: datetime = Field(
        description="When the invitation expires"
    )
    
    accepted_at: Optional[datetime] = Field(
        default=None,
        description="When the invitation was accepted"
    )
    
    declined_at: Optional[datetime] = Field(
        default=None,
        description="When the invitation was declined"
    )
    
    last_sent_at: datetime = Field(
        description="When the invitation was last sent"
    )
    
    send_count: int = Field(
        default=1,
        ge=1,
        title="Send Count", description="Number of times the invitation has been sent"
    )


class InviteAccept(BaseModel):
    """Schema for accepting an invitation."""
    
    token: str = Field(
        min_length=1, max_length=255,
        title="Token", description="Invitation token from the invitation URL"
    )
    
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        title="Password", description="Password for new user account (if needed)"
    )
    
    full_name: Optional[str] = Field(
        default=None,
        min_length=1, max_length=100,
        title="Full Name", description="Full name for new user account (if needed)"
    )
    
    terms_accepted: bool = Field(
        default=False,
        title="Terms Accepted", description="Whether user has accepted terms of service"
    )
    
    @validator('terms_accepted')
    def validate_terms_accepted(cls, v):
        """Validate that terms are accepted."""
        if not v:
            raise ValueError("Terms of service must be accepted")
        return v


class InviteDecline(BaseModel):
    """Schema for declining an invitation."""
    
    token: str = Field(
        min_length=1, max_length=255,
        title="Token", description="Invitation token"
    )
    
    reason: Optional[str] = Field(
        default=None,
        max_length=200,
        title="Reason", description="Optional reason for declining"
    )


class InviteListParams(BaseModel):
    """Parameters for listing invitations."""
    
    status: Optional[InviteStatus] = Field(
        default=None,
        title="Status Filter", description="Filter by invitation status"
    )
    
    invite_type: Optional[InviteType] = Field(
        default=None,
        title="Type Filter", description="Filter by invitation type"
    )
    
    role: Optional[str] = Field(
        default=None,
        title="Role Filter", description="Filter by assigned role"
    )
    
    invited_by: Optional[UUID] = Field(
        default=None,
        title="Invited By", description="Filter by who sent the invitation"
    )
    
    search: Optional[str] = Field(
        default=None,
        max_length=100,
        title="Search", description="Search in email addresses and messages"
    )
    
    created_after: Optional[datetime] = Field(
        default=None,
        title="Created After", description="Filter invitations created after this date"
    )
    
    expires_before: Optional[datetime] = Field(
        default=None,
        title="Expires Before", description="Filter invitations expiring before this date"
    )


class InviteResend(BaseModel):
    """Schema for resending an invitation."""
    
    message: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Updated Message", description="Updated custom message for the resend"
    )
    
    extend_expiration_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=30,
        title="Extend Expiration", description="Number of days to extend expiration (1-30)"
    )


class BulkInviteCreate(BaseModel):
    """Schema for creating multiple invitations."""
    
    invitations: List[InviteCreate] = Field(
        min_items=1,
        max_items=100,
        title="Invitations", description="List of invitations to create (max 100)"
    )
    
    send_immediately: bool = Field(
        default=True,
        title="Send Immediately", description="Whether to send invitation emails immediately"
    )


class BulkInviteResponse(BaseModel):
    """Schema for bulk invitation response."""
    
    successful_invites: List[InviteResponse] = Field(
        title="Successful Invites", description="Successfully created invitations"
    )
    
    failed_invites: List[Dict[str, Any]] = Field(
        title="Failed Invites", description="Failed invitations with error details"
    )
    
    total_requested: int = Field(
        title="Total Requested", description="Total number of invitations requested"
    )
    
    total_successful: int = Field(
        title="Total Successful", description="Number of successful invitations"
    )
    
    total_failed: int = Field(
        title="Total Failed", description="Number of failed invitations"
    )


class InviteStats(BaseModel):
    """Invitation statistics."""
    
    total_sent: int = Field(
        title="Total Sent", description="Total invitations sent"
    )
    
    pending: int = Field(
        title="Pending", description="Number of pending invitations"
    )
    
    accepted: int = Field(
        title="Accepted", description="Number of accepted invitations"
    )
    
    declined: int = Field(
        title="Declined", description="Number of declined invitations"
    )
    
    expired: int = Field(
        title="Expired", description="Number of expired invitations"
    )
    
    acceptance_rate: float = Field(
        title="Acceptance Rate", description="Invitation acceptance rate percentage"
    )
    
    avg_response_time_hours: Optional[float] = Field(
        default=None,
        title="Average Response Time", description="Average time to respond in hours"
    )
    
    last_7_days: Dict[str, int] = Field(
        title="Last 7 Days", description="Invitation activity in the last 7 days"
    )
