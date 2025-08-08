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
Organization schema module exports.
Provides schemas for organizations, members, teams, and invitations.
"""

# Core organization schemas
from .core import (
    OrganizationPlan,
    OrganizationStatus,
    OrganizationSettings,
    OrganizationLimits,
    OrganizationBase,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationStats,
    OrganizationListParams,
    OrganizationTransfer,
)

# Member management schemas
from .members import (
    MemberRole,
    MemberStatus,
    MemberJoinMethod,
    MemberAdd,
    MemberUpdate,
    MemberResponse,
    MemberListParams,
    MemberRemove,
    BulkMemberAction,
    BulkMemberActionResponse,
    MemberActivity,
    MemberExport,
)

# Team management schemas
from .teams import (
    TeamRole,
    TeamVisibility,
    TeamStatus,
    TeamCreate,
    TeamUpdate,
    TeamMember,
    TeamResponse,
    TeamMemberAdd,
    TeamMemberUpdate,
    TeamMemberRemove,
    TeamListParams,
    TeamStats,
    BulkTeamMemberAction,
)

# Invitation management schemas
from .invites import (
    InviteStatus,
    InviteType,
    InviteCreate,
    InviteUpdate,
    InviteResponse,
    InviteAccept,
    InviteDecline,
    InviteListParams,
    InviteResend,
    BulkInviteCreate,
    BulkInviteResponse,
    InviteStats,
)

__all__ = [
    # Core organization schemas
    "OrganizationPlan",
    "OrganizationStatus",
    "OrganizationSettings",
    "OrganizationLimits",
    "OrganizationBase",
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    "OrganizationStats",
    "OrganizationListParams",
    "OrganizationTransfer",
    
    # Member schemas
    "MemberRole",
    "MemberStatus",
    "MemberJoinMethod",
    "MemberAdd",
    "MemberUpdate",
    "MemberResponse",
    "MemberListParams",
    "MemberRemove",
    "BulkMemberAction",
    "BulkMemberActionResponse",
    "MemberActivity",
    "MemberExport",
    
    # Team schemas
    "TeamRole",
    "TeamVisibility",
    "TeamStatus",
    "TeamCreate",
    "TeamUpdate",
    "TeamMember",
    "TeamResponse",
    "TeamMemberAdd",
    "TeamMemberUpdate",
    "TeamMemberRemove",
    "TeamListParams",
    "TeamStats",
    "BulkTeamMemberAction",
    
    # Invitation schemas
    "InviteStatus",
    "InviteType",
    "InviteCreate",
    "InviteUpdate",
    "InviteResponse",
    "InviteAccept",
    "InviteDecline",
    "InviteListParams",
    "InviteResend",
    "BulkInviteCreate",
    "BulkInviteResponse",
    "InviteStats",
]
