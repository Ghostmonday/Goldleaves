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
Organization core schemas for organization management.
Provides schemas for creating, updating, and managing organizations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from ..dependencies import (
    create_field_metadata,
    email_field,
    validate_non_empty_string,
    validate_slug,
)


class OrganizationPlan(str, Enum):
    """Organization subscription plans."""
    FREE = "free"
    STARTUP = "startup"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class OrganizationStatus(str, Enum):
    """Organization status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class OrganizationSettings(BaseModel):
    """Organization settings schema."""
    
    allow_public_signup: bool = Field(
        default=False,
        title="Allow Public Signup", description="Whether users can join this organization without invitation"
    )
    
    require_2fa: bool = Field(
        default=False,
        title="Require 2FA", description="Whether two-factor authentication is required for all members"
    )
    
    allowed_email_domains: Optional[List[str]] = Field(
        default=None,
        **create_field_metadata(
            title="Allowed Email Domains",
            description="Email domains allowed for automatic membership",
            example=["company.com", "subsidiary.com"]
        )
    )
    
    default_role: Optional[str] = Field(
        default="member",
        title="Default Role", description="Default role for new members"
    )
    
    session_timeout_minutes: int = Field(
        default=480,  # 8 hours
        ge=30,
        le=1440,
        title="Session Timeout", description="Session timeout in minutes (30-1440)"
    )
    
    max_file_size_mb: int = Field(
        default=100,
        ge=1,
        le=1000,
        title="Max File Size", description="Maximum file upload size in MB"
    )
    
    custom_branding: Optional[Dict[str, str]] = Field(
        default=None,
        title="Custom Branding", description="Custom branding settings (logo, colors, etc.)"
    )


class OrganizationLimits(BaseModel):
    """Organization plan limits."""
    
    max_members: Optional[int] = Field(
        default=None,
        title="Max Members", description="Maximum number of members (null for unlimited)"
    )
    
    max_teams: Optional[int] = Field(
        default=None,
        title="Max Teams", description="Maximum number of teams (null for unlimited)"
    )
    
    max_documents: Optional[int] = Field(
        default=None,
        title="Max Documents", description="Maximum number of documents (null for unlimited)"
    )
    
    max_storage_gb: Optional[int] = Field(
        default=None,
        title="Max Storage", description="Maximum storage in GB (null for unlimited)"
    )
    
    api_requests_per_hour: int = Field(
        default=1000,
        title="API Requests Per Hour", description="Maximum API requests per hour"
    )
    
    features: List[str] = Field(
        default_factory=list,
        **create_field_metadata(
            title="Features",
            description="List of enabled features for this plan",
            example=["advanced_analytics", "sso", "custom_integrations"]
        )
    )


class OrganizationBase(BaseModel):
    """Base organization fields."""
    
    name: str = Field(
        min_length=2, max_length=100,
        title="Organization Name", description="Name of the organization", example="Acme Corporation"
    )
    
    slug: str = Field(
        min_length=2,
        max_length=50,
        pattern="^[a-z0-9-]+$",
        title="Organization Slug", description="URL-safe identifier for the organization", example="acme-corp"
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Description", description="Brief description of the organization"
    )
    
    @validator('name')
    def validate_name(cls, v):
        """Validate organization name."""
        return validate_non_empty_string(v)
    
    @validator('slug')
    def validate_slug(cls, v):
        """Validate organization slug."""
        return validate_slug(v)


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""
    
    owner_email: str = Field(
        **email_field(),
        title="Owner Email", description="Email address of the organization owner", example="owner@acme.com"
    )
    
    plan: OrganizationPlan = Field(
        default=OrganizationPlan.FREE,
        title="Plan", description="Initial subscription plan"
    )
    
    settings: Optional[OrganizationSettings] = Field(
        default=None,
        title="Settings", description="Initial organization settings"
    )
    
    invite_members: Optional[List[str]] = Field(
        default=None,
        title="Invite Members", description="Email addresses to invite as initial members"
    )


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=2, max_length=100
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=500
    )
    
    settings: Optional[OrganizationSettings] = Field(
        default=None
    )
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            return validate_non_empty_string(v)
        return v


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""
    
    id: UUID = Field(
        description="Unique organization identifier"
    )
    
    plan: OrganizationPlan = Field(
        title="Plan", description="Current subscription plan"
    )
    
    status: OrganizationStatus = Field(
        title="Status", description="Current organization status"
    )
    
    owner_id: UUID = Field(
        description="Organization owner user ID"
    )
    
    member_count: int = Field(
        ge=0,
        title="Member Count", description="Total number of organization members"
    )
    
    team_count: int = Field(
        default=0,
        ge=0,
        title="Team Count", description="Total number of teams"
    )
    
    document_count: int = Field(
        default=0,
        ge=0,
        title="Document Count", description="Total number of documents"
    )
    
    storage_used_gb: float = Field(
        default=0.0,
        ge=0.0,
        title="Storage Used", description="Storage used in GB"
    )
    
    limits: OrganizationLimits = Field(
        title="Limits", description="Plan-based limits and features"
    )
    
    settings: OrganizationSettings = Field(
        title="Settings", description="Organization settings"
    )
    
    created_at: datetime = Field(
        description="When the organization was created"
    )
    
    updated_at: datetime = Field(
        description="When the organization was last updated"
    )
    
    last_activity_at: Optional[datetime] = Field(
        default=None,
        description="Last activity in the organization"
    )


class OrganizationStats(BaseModel):
    """Organization statistics and analytics."""
    
    members: Dict[str, int] = Field(
        **create_field_metadata(
            title="Member Statistics",
            description="Member count by role, status, etc.",
            example={"active": 25, "pending": 3, "admins": 2}
        )
    )
    
    teams: Dict[str, int] = Field(
        title="Team Statistics", description="Team statistics"
    )
    
    documents: Dict[str, int] = Field(
        title="Document Statistics", description="Document statistics by type, status, etc."
    )
    
    storage: Dict[str, float] = Field(
        title="Storage Statistics", description="Storage usage statistics"
    )
    
    activity: Dict[str, int] = Field(
        title="Activity Statistics", description="Activity metrics for the last 30 days"
    )
    
    billing: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Billing Statistics", description="Billing and usage metrics"
    )


class OrganizationListParams(BaseModel):
    """Parameters for listing organizations."""
    
    status: Optional[OrganizationStatus] = Field(
        default=None,
        title="Status Filter", description="Filter by organization status"
    )
    
    plan: Optional[OrganizationPlan] = Field(
        default=None,
        title="Plan Filter", description="Filter by subscription plan"
    )
    
    search: Optional[str] = Field(
        default=None,
        max_length=100,
        title="Search", description="Search in organization names and descriptions"
    )
    
    created_after: Optional[datetime] = Field(
        default=None,
        title="Created After", description="Filter organizations created after this date"
    )
    
    owner_id: Optional[UUID] = Field(
        default=None,
        title="Owner ID", description="Filter by owner user ID"
    )


class OrganizationTransfer(BaseModel):
    """Schema for transferring organization ownership."""
    
    new_owner_email: str = Field(
        **email_field(),
        title="New Owner Email", description="Email of the new organization owner"
    )
    
    transfer_reason: Optional[str] = Field(
        default=None,
        max_length=200,
        title="Transfer Reason", description="Reason for ownership transfer"
    )
    
    notify_members: bool = Field(
        default=True,
        title="Notify Members", description="Whether to notify organization members about the transfer"
    )
