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
Team management schemas for organizing members.
Provides schemas for creating, managing, and organizing teams within organizations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from ..dependencies import validate_non_empty_string, validate_slug


class TeamRole(str, Enum):
    """Team member roles."""
    LEAD = "lead"
    MEMBER = "member"
    CONTRIBUTOR = "contributor"
    OBSERVER = "observer"


class TeamVisibility(str, Enum):
    """Team visibility settings."""
    PUBLIC = "public"        # Visible to all organization members
    PRIVATE = "private"      # Visible only to team members
    RESTRICTED = "restricted"  # Visible to team members and specific roles


class TeamStatus(str, Enum):
    """Team status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class TeamCreate(BaseModel):
    """Schema for creating a new team."""
    
    name: str = Field(
        min_length=2, max_length=50,
        title="Team Name", description="Name of the team", example="Engineering Team"
    )
    
    slug: str = Field(
        min_length=2,
        max_length=30,
        pattern="^[a-z0-9-]+$",
        title="Team Slug", description="URL-safe identifier for the team", example="engineering"
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Description", description="Brief description of the team's purpose"
    )
    
    visibility: TeamVisibility = Field(
        default=TeamVisibility.PUBLIC,
        title="Visibility", description="Who can see this team"
    )
    
    parent_team_id: Optional[UUID] = Field(
        default=None,
        title="Parent Team ID", description="Parent team for hierarchical organization"
    )
    
    initial_members: Optional[List[UUID]] = Field(
        default=None,
        title="Initial Members", description="User IDs to add as initial team members"
    )
    
    settings: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Settings", description="Team-specific settings and preferences"
    )
    
    @validator('name')
    def validate_name(cls, v):
        """Validate team name."""
        return validate_non_empty_string(v)
    
    @validator('slug')
    def validate_slug(cls, v):
        """Validate team slug."""
        return validate_slug(v)


class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=2, max_length=50
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=500
    )
    
    visibility: Optional[TeamVisibility] = Field(
        default=None
    )
    
    status: Optional[TeamStatus] = Field(
        default=None
    )
    
    parent_team_id: Optional[UUID] = Field(
        default=None
    )
    
    settings: Optional[Dict[str, Any]] = Field(
        default=None
    )
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            return validate_non_empty_string(v)
        return v


class TeamMember(BaseModel):
    """Team member information."""
    
    user_id: UUID = Field(
        description="User ID"
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
        title="Avatar URL", description="Member's avatar image URL"
    )
    
    team_role: TeamRole = Field(
        title="Team Role", description="Member's role within the team"
    )
    
    joined_team_at: datetime = Field(
        description="When the member joined the team"
    )
    
    added_by: Optional[UUID] = Field(
        default=None,
        description="User who added this member to the team"
    )


class TeamResponse(BaseModel):
    """Schema for team response."""
    
    id: UUID = Field(
        description="Unique team identifier"
    )
    
    organization_id: UUID = Field(
        description="Organization ID"
    )
    
    name: str = Field(
        title="Name", description="Team name"
    )
    
    slug: str = Field(
        title="Slug", description="Team slug"
    )
    
    description: Optional[str] = Field(
        title="Description", description="Team description"
    )
    
    visibility: TeamVisibility = Field(
        title="Visibility", description="Team visibility setting"
    )
    
    status: TeamStatus = Field(
        title="Status", description="Current team status"
    )
    
    parent_team_id: Optional[UUID] = Field(
        default=None,
        title="Parent Team ID", description="Parent team (if this is a sub-team)"
    )
    
    member_count: int = Field(
        default=0,
        ge=0,
        title="Member Count", description="Total number of team members"
    )
    
    document_count: int = Field(
        default=0,
        ge=0,
        title="Document Count", description="Number of documents owned by this team"
    )
    
    members: Optional[List[TeamMember]] = Field(
        default=None,
        title="Members", description="Team members (if requested)"
    )
    
    child_teams: Optional[List['TeamResponse']] = Field(
        default=None,
        title="Child Teams", description="Sub-teams (if requested)"
    )
    
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        title="Settings", description="Team settings"
    )
    
    created_at: datetime = Field(
        description="When the team was created"
    )
    
    updated_at: datetime = Field(
        description="When the team was last updated"
    )
    
    created_by: UUID = Field(
        description="User who created the team"
    )


class TeamMemberAdd(BaseModel):
    """Schema for adding a member to a team."""
    
    user_id: UUID = Field(
        description="User ID to add to the team"
    )
    
    role: TeamRole = Field(
        default=TeamRole.MEMBER,
        title="Role", description="Role to assign to the member in this team"
    )
    
    notify_member: bool = Field(
        default=True,
        title="Notify Member", description="Whether to notify the member about being added"
    )


class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member."""
    
    role: TeamRole = Field(
        title="Role", description="New role for the team member"
    )


class TeamMemberRemove(BaseModel):
    """Schema for removing a member from a team."""
    
    reason: Optional[str] = Field(
        default=None,
        max_length=200,
        title="Reason", description="Reason for removing the member"
    )
    
    notify_member: bool = Field(
        default=True,
        title="Notify Member", description="Whether to notify the member about removal"
    )


class TeamListParams(BaseModel):
    """Parameters for listing teams."""
    
    status: Optional[TeamStatus] = Field(
        default=None,
        title="Status Filter", description="Filter by team status"
    )
    
    visibility: Optional[TeamVisibility] = Field(
        default=None,
        title="Visibility Filter", description="Filter by team visibility"
    )
    
    parent_team_id: Optional[UUID] = Field(
        default=None,
        title="Parent Team ID", description="Filter by parent team (null for top-level teams)"
    )
    
    member_id: Optional[UUID] = Field(
        default=None,
        title="Member ID", description="Filter teams that include this member"
    )
    
    search: Optional[str] = Field(
        default=None,
        max_length=100,
        title="Search", description="Search in team names and descriptions"
    )
    
    include_members: bool = Field(
        default=False,
        title="Include Members", description="Whether to include member details in response"
    )
    
    include_child_teams: bool = Field(
        default=False,
        title="Include Child Teams", description="Whether to include sub-teams in response"
    )


class TeamStats(BaseModel):
    """Team statistics and analytics."""
    
    total_members: int = Field(
        title="Total Members", description="Total number of team members"
    )
    
    members_by_role: Dict[str, int] = Field(
        title="Members by Role", description="Member count breakdown by team role"
    )
    
    total_documents: int = Field(
        title="Total Documents", description="Total documents created by team"
    )
    
    documents_last_30_days: int = Field(
        title="Documents Last 30 Days", description="Documents created in the last 30 days"
    )
    
    activity_score: float = Field(
        title="Activity Score", description="Team activity score (0-100)"
    )
    
    last_activity_at: Optional[datetime] = Field(
        description="Last team activity"
    )
    
    top_contributors: List[Dict[str, Any]] = Field(
        title="Top Contributors", description="Most active team members"
    )


class BulkTeamMemberAction(BaseModel):
    """Schema for bulk team member operations."""
    
    user_ids: List[UUID] = Field(
        min_items=1,
        max_items=50,
        title="User IDs", description="List of user IDs to perform action on (max 50)"
    )
    
    action: str = Field(
        title="Action", description="Action to perform: 'add', 'remove', 'update_role'"
    )
    
    role: Optional[TeamRole] = Field(
        default=None,
        title="Role", description="Role for add/update_role actions"
    )
    
    notify_members: bool = Field(
        default=True,
        title="Notify Members", description="Whether to notify affected members"
    )


# Forward reference for self-referencing model
TeamResponse.model_rebuild()
