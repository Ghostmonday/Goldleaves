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
Organization member management schemas.
Provides schemas for managing organization members, roles, and permissions.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID

from ..dependencies import (
    non_empty_string,
    uuid_field,
    timestamp_field,
    email_field,
    validate_non_empty_string,
    create_field_metadata,
    Status
)


class MemberRole(str, Enum):
    """Organization member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    GUEST = "guest"


class MemberStatus(str, Enum):
    """Member status in organization."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    LEFT = "left"


class MemberJoinMethod(str, Enum):
    """How member joined the organization."""
    INVITED = "invited"
    SIGNUP = "signup"
    DOMAIN_AUTO_JOIN = "domain_auto_join"
    API = "api"
    IMPORT = "import"


class MemberAdd(BaseModel):
    """Schema for adding a member to organization."""
    
    email: str = Field(
        **email_field(),
        title="Email", description="Email address of the user to add", example="user@example.com"
    )
    
    role: MemberRole = Field(
        default=MemberRole.MEMBER,
        title="Role", description="Role to assign to the member"
    )
    
    team_ids: Optional[List[UUID]] = Field(
        default=None,
        title="Team IDs", description="Teams to add the member to"
    )
    
    send_invitation: bool = Field(
        default=True,
        title="Send Invitation", description="Whether to send an invitation email"
    )
    
    custom_message: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Custom Message", description="Custom message to include in invitation"
    )


class MemberUpdate(BaseModel):
    """Schema for updating a member."""
    
    role: Optional[MemberRole] = Field(
        default=None,
        title="Role", description="New role for the member"
    )
    
    status: Optional[MemberStatus] = Field(
        default=None,
        title="Status", description="New status for the member"
    )
    
    team_ids: Optional[List[UUID]] = Field(
        default=None,
        title="Team IDs", description="Teams the member should belong to"
    )
    
    custom_permissions: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Custom Permissions", description="Custom permissions for this member"
    )


class MemberResponse(BaseModel):
    """Schema for member response."""
    
    id: UUID = Field(
        description="Unique membership identifier"
    )
    
    user_id: UUID = Field(
        description="User ID"
    )
    
    organization_id: UUID = Field(
        description="Organization ID"
    )
    
    email: str = Field(
        title="Email", description="Member email address"
    )
    
    full_name: Optional[str] = Field(
        default=None,
        title="Full Name", description="Member's full name"
    )
    
    avatar_url: Optional[str] = Field(
        default=None,
        title="Avatar URL", description="URL to member's avatar image"
    )
    
    role: MemberRole = Field(
        title="Role", description="Member's role in the organization"
    )
    
    status: MemberStatus = Field(
        title="Status", description="Member's current status"
    )
    
    join_method: MemberJoinMethod = Field(
        title="Join Method", description="How the member joined the organization"
    )
    
    teams: List[Dict[str, Any]] = Field(
        default_factory=list,
        title="Teams", description="Teams the member belongs to"
    )
    
    permissions: Dict[str, Any] = Field(
        default_factory=dict,
        title="Permissions", description="Effective permissions for this member"
    )
    
    last_login_at: Optional[datetime] = Field(
        default=None,
        description="Last login timestamp"
    )
    
    last_activity_at: Optional[datetime] = Field(
        default=None,
        description="Last activity timestamp"
    )
    
    joined_at: datetime = Field(
        description="When the member joined"
    )
    
    updated_at: datetime = Field(
        description="When the membership was last updated"
    )
    
    invited_by: Optional[UUID] = Field(
        default=None,
        description="User who invited this member"
    )


class MemberListParams(BaseModel):
    """Parameters for listing organization members."""
    
    role: Optional[MemberRole] = Field(
        default=None,
        title="Role Filter", description="Filter by member role"
    )
    
    status: Optional[MemberStatus] = Field(
        default=None,
        title="Status Filter", description="Filter by member status"
    )
    
    team_id: Optional[UUID] = Field(
        default=None,
        title="Team ID", description="Filter by team membership"
    )
    
    search: Optional[str] = Field(
        default=None,
        max_length=100,
        title="Search", description="Search in names and email addresses"
    )
    
    joined_after: Optional[datetime] = Field(
        default=None,
        title="Joined After", description="Filter members who joined after this date"
    )
    
    has_logged_in: Optional[bool] = Field(
        default=None,
        title="Has Logged In", description="Filter by whether member has ever logged in"
    )


class MemberRemove(BaseModel):
    """Schema for removing a member from organization."""
    
    reason: Optional[str] = Field(
        default=None,
        max_length=200,
        title="Reason", description="Reason for removing the member"
    )
    
    transfer_ownership: Optional[UUID] = Field(
        default=None,
        title="Transfer Ownership", description="User ID to transfer owned resources to"
    )
    
    notify_member: bool = Field(
        default=True,
        title="Notify Member", description="Whether to notify the member about removal"
    )


class BulkMemberAction(BaseModel):
    """Schema for bulk member operations."""
    
    member_ids: List[UUID] = Field(
        min_items=1,
        max_items=100,
        title="Member IDs", description="List of member IDs to perform action on (max 100)"
    )
    
    action: str = Field(
        title="Action", description="Action to perform: 'update_role', 'change_status', 'add_to_team', etc."
    )
    
    parameters: Dict[str, Any] = Field(
        title="Parameters", description="Parameters for the bulk action"
    )


class BulkMemberActionResponse(BaseModel):
    """Schema for bulk member action response."""
    
    successful_operations: List[Dict[str, Any]] = Field(
        title="Successful Operations", description="Operations that completed successfully"
    )
    
    failed_operations: List[Dict[str, Any]] = Field(
        title="Failed Operations", description="Operations that failed with error details"
    )
    
    total_requested: int = Field(
        title="Total Requested", description="Total number of operations requested"
    )
    
    total_successful: int = Field(
        title="Total Successful", description="Number of successful operations"
    )
    
    total_failed: int = Field(
        title="Total Failed", description="Number of failed operations"
    )


class MemberActivity(BaseModel):
    """Member activity information."""
    
    total_documents_created: int = Field(
        default=0,
        title="Documents Created", description="Total documents created by member"
    )
    
    total_documents_edited: int = Field(
        default=0,
        title="Documents Edited", description="Total documents edited by member"
    )
    
    total_comments: int = Field(
        default=0,
        title="Comments", description="Total comments made by member"
    )
    
    total_login_sessions: int = Field(
        default=0,
        title="Login Sessions", description="Total number of login sessions"
    )
    
    avg_session_duration_minutes: Optional[float] = Field(
        default=None,
        title="Average Session Duration", description="Average session duration in minutes"
    )
    
    last_7_days_activity: Dict[str, int] = Field(
        default_factory=dict,
        title="Last 7 Days Activity", description="Activity breakdown for the last 7 days"
    )
    
    most_used_features: List[str] = Field(
        default_factory=list,
        title="Most Used Features", description="Features most frequently used by member"
    )


class MemberExport(BaseModel):
    """Schema for member data export."""
    
    format: str = Field(
        default="csv",
        title="Export Format", description="Export format: csv, xlsx, json"
    )
    
    include_activity: bool = Field(
        default=False,
        title="Include Activity", description="Whether to include activity data in export"
    )
    
    include_permissions: bool = Field(
        default=False,
        title="Include Permissions", description="Whether to include permission details"
    )
    
    date_range: Optional[Dict[str, datetime]] = Field(
        default=None,
        title="Date Range", description="Date range for activity data"
    )
