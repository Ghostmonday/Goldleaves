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
Document sharing and permissions schemas.
Provides schemas for document sharing, access control, and collaboration permissions.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
from uuid import UUID



class ShareType(str, Enum):
    """Type of sharing."""
    PRIVATE = "private"
    INTERNAL = "internal"
    PUBLIC = "public"
    LINK = "link"
    DOMAIN = "domain"


class AccessLevel(str, Enum):
    """Access level for shared documents."""
    VIEWER = "viewer"
    COMMENTER = "commenter"
    EDITOR = "editor"
    OWNER = "owner"


class ShareStatus(str, Enum):
    """Share status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class LinkAccess(str, Enum):
    """Link access restrictions."""
    ANYONE = "anyone"
    ORGANIZATION = "organization"
    SPECIFIC_USERS = "specific_users"
    PASSWORD_PROTECTED = "password_protected"


class DocumentShareCreate(BaseModel):
    """Schema for creating a document share."""
    
    share_type: ShareType = Field(
        title="Share Type", description="Type of sharing to create"
    )
    
    access_level: AccessLevel = Field(
        title="Access Level", description="Level of access to grant"
    )
    
    # For user/group sharing
    user_ids: Optional[List[UUID]] = Field(
        default=None,
        title="User IDs", description="List of user IDs to share with (for INTERNAL type)"
    )
    
    group_ids: Optional[List[UUID]] = Field(
        default=None,
        title="Group IDs", description="List of group IDs to share with"
    )
    
    # For email invitations
    email_addresses: Optional[List[str]] = Field(
        default=None,
        title="Email Addresses", description="List of email addresses to invite"
    )
    
    # For link sharing
    link_access: Optional[LinkAccess] = Field(
        default=None,
        title="Link Access", description="Link access restrictions (for LINK type)"
    )
    
    link_password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=50,
        title="Link Password", description="Password for link access (if PASSWORD_PROTECTED)"
    )
    
    # For domain sharing
    allowed_domains: Optional[List[str]] = Field(
        default=None,
        title="Allowed Domains", description="List of allowed email domains (for DOMAIN type)"
    )
    
    # General options
    expires_at: Optional[datetime] = Field(
        default=None,
        title="Expires At", description="When the share expires (optional)"
    )
    
    message: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Message", description="Optional message to include with the share"
    )
    
    notify_users: bool = Field(
        default=True,
        title="Notify Users", description="Whether to send notification emails"
    )
    
    allow_download: bool = Field(
        default=True,
        title="Allow Download", description="Whether to allow downloading the document"
    )
    
    allow_copy: bool = Field(
        default=True,
        title="Allow Copy", description="Whether to allow copying the document"
    )
    
    allow_print: bool = Field(
        default=True,
        title="Allow Print", description="Whether to allow printing the document"
    )
    
    require_login: bool = Field(
        default=False,
        title="Require Login", description="Whether viewing requires user login"
    )
    
    @validator('email_addresses')
    def validate_emails(cls, v):
        """Validate email addresses format."""
        if v:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            for email in v:
                if not re.match(email_pattern, email):
                    raise ValueError(f"Invalid email address: {email}")
        return v
    
    @validator('allowed_domains')
    def validate_domains(cls, v):
        """Validate domain format."""
        if v:
            import re
            domain_pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            for domain in v:
                if not re.match(domain_pattern, domain):
                    raise ValueError(f"Invalid domain: {domain}")
        return v


class DocumentShareUpdate(BaseModel):
    """Schema for updating a document share."""
    
    access_level: Optional[AccessLevel] = Field(
        default=None
    )
    
    expires_at: Optional[datetime] = Field(
        default=None
    )
    
    allow_download: Optional[bool] = Field(
        default=None
    )
    
    allow_copy: Optional[bool] = Field(
        default=None
    )
    
    allow_print: Optional[bool] = Field(
        default=None
    )
    
    require_login: Optional[bool] = Field(
        default=None
    )
    
    status: Optional[ShareStatus] = Field(
        default=None
    )


class DocumentShareResponse(BaseModel):
    """Schema for document share response."""
    
    id: UUID = Field(
        description="Unique share identifier"
    )
    
    document_id: UUID = Field(
        description="Document ID"
    )
    
    document_title: str = Field(
        title="Document Title", description="Title of the shared document"
    )
    
    share_type: ShareType = Field(
        title="Share Type", description="Type of sharing"
    )
    
    access_level: AccessLevel = Field(
        title="Access Level", description="Level of access granted"
    )
    
    status: ShareStatus = Field(
        title="Status", description="Current share status"
    )
    
    created_by: UUID = Field(
        description="User who created the share"
    )
    
    created_by_name: str = Field(
        title="Created By Name", description="Display name of user who created the share"
    )
    
    # Share-specific details
    user_id: Optional[UUID] = Field(
        default=None,
        description="User ID (for user-specific shares)"
    )
    
    user_name: Optional[str] = Field(
        default=None,
        title="User Name", description="Display name of shared user"
    )
    
    user_email: Optional[str] = Field(
        default=None,
        title="User Email", description="Email of shared user"
    )
    
    group_id: Optional[UUID] = Field(
        default=None,
        description="Group ID (for group shares)"
    )
    
    group_name: Optional[str] = Field(
        default=None,
        title="Group Name", description="Name of shared group"
    )
    
    # Link sharing details
    share_link: Optional[str] = Field(
        default=None,
        title="Share Link", description="Public sharing link (for LINK type)"
    )
    
    link_access: Optional[LinkAccess] = Field(
        default=None,
        title="Link Access", description="Link access restrictions"
    )
    
    has_password: Optional[bool] = Field(
        default=None,
        title="Has Password", description="Whether link is password protected"
    )
    
    allowed_domains: Optional[List[str]] = Field(
        default=None,
        title="Allowed Domains", description="Allowed email domains"
    )
    
    # Permissions
    allow_download: bool = Field(
        title="Allow Download", description="Whether downloading is allowed"
    )
    
    allow_copy: bool = Field(
        title="Allow Copy", description="Whether copying is allowed"
    )
    
    allow_print: bool = Field(
        title="Allow Print", description="Whether printing is allowed"
    )
    
    require_login: bool = Field(
        title="Require Login", description="Whether login is required"
    )
    
    # Timestamps
    created_at: datetime = Field(
        description="When the share was created"
    )
    
    updated_at: Optional[datetime] = Field(
        default=None,
        description="When the share was last updated"
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When the share expires"
    )
    
    last_accessed: Optional[datetime] = Field(
        default=None,
        description="When the share was last accessed"
    )
    
    access_count: int = Field(
        default=0,
        title="Access Count", description="Number of times the share has been accessed"
    )


class ShareLinkAccessRequest(BaseModel):
    """Schema for accessing a document via share link."""
    
    password: Optional[str] = Field(
        default=None,
        title="Password", description="Password for password-protected links"
    )


class DocumentPermissionCheck(BaseModel):
    """Schema for checking document permissions."""
    
    user_id: UUID = Field(
        description="User ID to check permissions for"
    )
    
    action: str = Field(
        title="Action", description="Action to check: 'read', 'write', 'comment', 'share', 'delete'", example="read"
    )
    
    @validator('action')
    def validate_action(cls, v):
        """Validate permission action."""
        allowed_actions = ['read', 'write', 'comment', 'share', 'delete']
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {', '.join(allowed_actions)}")
        return v


class DocumentPermissionResponse(BaseModel):
    """Schema for document permission response."""
    
    has_permission: bool = Field(
        title="Has Permission", description="Whether the user has the requested permission"
    )
    
    access_level: Optional[AccessLevel] = Field(
        default=None,
        title="Access Level", description="User's access level to the document"
    )
    
    permission_source: Optional[str] = Field(
        default=None,
        title="Permission Source", description="Source of permission: 'owner', 'direct_share', 'group_share', 'public'"
    )


class ShareListParams(BaseModel):
    """Parameters for listing document shares."""
    
    share_type: Optional[ShareType] = Field(
        default=None,
        title="Share Type Filter", description="Filter by share type"
    )
    
    access_level: Optional[AccessLevel] = Field(
        default=None,
        title="Access Level Filter", description="Filter by access level"
    )
    
    status: Optional[ShareStatus] = Field(
        default=None,
        title="Status Filter", description="Filter by share status"
    )
    
    created_by: Optional[UUID] = Field(
        default=None,
        title="Created By Filter", description="Filter by share creator"
    )
    
    include_expired: bool = Field(
        default=False,
        title="Include Expired", description="Whether to include expired shares"
    )


class ShareStats(BaseModel):
    """Share statistics for a document."""
    
    total_shares: int = Field(
        title="Total Shares", description="Total number of shares"
    )
    
    active_shares: int = Field(
        title="Active Shares", description="Number of active shares"
    )
    
    shares_by_type: Dict[str, int] = Field(
        title="Shares by Type", description="Share count breakdown by type"
    )
    
    shares_by_access_level: Dict[str, int] = Field(
        title="Shares by Access Level", description="Share count breakdown by access level"
    )
    
    total_access_count: int = Field(
        title="Total Access Count", description="Total number of times document has been accessed via shares"
    )
    
    unique_viewers: int = Field(
        title="Unique Viewers", description="Number of unique users who have accessed the document"
    )
    
    last_accessed: Optional[datetime] = Field(
        default=None,
        description="When the document was last accessed via a share"
    )
    
    most_popular_share_type: Optional[str] = Field(
        default=None,
        title="Most Popular Share Type", description="Most frequently used share type"
    )


class BulkShareAction(BaseModel):
    """Schema for bulk share operations."""
    
    share_ids: List[UUID] = Field(
        min_items=1,
        max_items=100,
        title="Share IDs", description="List of share IDs to operate on (max 100)"
    )
    
    action: str = Field(
        title="Action", description="Action to perform: 'revoke', 'extend', 'update_access'"
    )
    
    # For extend action
    extend_by_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        title="Extend By Days", description="Number of days to extend expiration (for 'extend' action)"
    )
    
    # For update_access action
    new_access_level: Optional[AccessLevel] = Field(
        default=None,
        title="New Access Level", description="New access level (for 'update_access' action)"
    )
    
    @validator('action')
    def validate_action(cls, v):
        """Validate bulk action."""
        allowed_actions = ['revoke', 'extend', 'update_access']
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {', '.join(allowed_actions)}")
        return v
