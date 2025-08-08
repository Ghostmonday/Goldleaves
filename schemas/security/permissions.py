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
Permission and role management schemas for authorization.
Provides schemas for roles, permissions, and access control.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Set
from datetime import datetime
from enum import Enum
from uuid import UUID

from ..dependencies import (
    non_empty_string,
    uuid_field,
    timestamp_field,
    validate_non_empty_string,
    create_field_metadata,
    PermissionLevel
)


class ResourceType(str, Enum):
    """Types of resources that can have permissions."""
    ORGANIZATION = "organization"
    TEAM = "team"
    DOCUMENT = "document"
    USER = "user"
    WEBHOOK = "webhook"
    API_KEY = "api_key"
    ADMIN = "admin"


class Action(str, Enum):
    """Available actions for permissions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"
    INVITE = "invite"
    REVOKE = "revoke"
    SHARE = "share"
    ADMIN = "admin"


class Permission(BaseModel):
    """Individual permission definition."""
    
    resource_type: ResourceType = Field(
        title="Resource Type", description="Type of resource this permission applies to"
    )
    
    action: Action = Field(
        title="Action", description="Action allowed on the resource"
    )
    
    resource_id: Optional[UUID] = Field(
        default=None,
        title="Resource ID", description="Specific resource ID (null for all resources of type)"
    )
    
    conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        **create_field_metadata(
            title="Conditions",
            description="Additional conditions for this permission",
            example={"owner_only": True, "department": "engineering"}
        )
    )
    
    def __str__(self) -> str:
        """String representation of permission."""
        resource = f"{self.resource_type.value}:{self.resource_id}" if self.resource_id else self.resource_type.value
        return f"{self.action.value}:{resource}"


class RoleCreate(BaseModel):
    """Schema for creating a new role."""
    
    name: str = Field(
        min_length=1, max_length=50,
        title="Role Name", description="Unique name for the role", example="Document Editor"
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=200,
        title="Description", description="Description of the role's purpose", example="Can create and edit documents but not delete them"
    )
    
    permissions: List[Permission] = Field(
        default_factory=list,
        title="Permissions", description="List of permissions granted to this role"
    )
    
    is_system_role: bool = Field(
        default=False,
        title="System Role", description="Whether this is a built-in system role"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        title="Organization ID", description="Organization this role belongs to (null for global roles)"
    )
    
    @validator('name')
    def validate_name(cls, v):
        """Validate role name."""
        return validate_non_empty_string(v)
    
    @validator('permissions')
    def validate_permissions(cls, v):
        """Validate permissions list."""
        # Check for duplicate permissions
        permission_strings = [str(p) for p in v]
        if len(permission_strings) != len(set(permission_strings)):
            raise ValueError("Duplicate permissions are not allowed")
        
        return v


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=1, max_length=50
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=200
    )
    
    permissions: Optional[List[Permission]] = Field(
        default=None
    )


class RoleResponse(BaseModel):
    """Schema for role response."""
    
    id: UUID = Field(
        description="Unique role identifier"
    )
    
    name: str = Field(
        title="Name", description="Role name"
    )
    
    description: Optional[str] = Field(
        title="Description", description="Role description"
    )
    
    permissions: List[Permission] = Field(
        title="Permissions", description="Permissions granted to this role"
    )
    
    is_system_role: bool = Field(
        title="System Role", description="Whether this is a built-in system role"
    )
    
    organization_id: Optional[UUID] = Field(
        title="Organization ID", description="Organization this role belongs to"
    )
    
    user_count: int = Field(
        default=0,
        title="User Count", description="Number of users assigned to this role"
    )
    
    created_at: datetime = Field(
        description="When the role was created"
    )
    
    updated_at: datetime = Field(
        description="When the role was last updated"
    )
    
    created_by: UUID = Field(
        description="User who created this role"
    )


class UserRoleAssignment(BaseModel):
    """Schema for assigning roles to users."""
    
    user_id: UUID = Field(
        description="User to assign role to"
    )
    
    role_id: UUID = Field(
        description="Role to assign"
    )
    
    scope: Optional[str] = Field(
        default=None,
        title="Scope", description="Scope of the role assignment (e.g., 'organization:123')", example="team:456"
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When this role assignment expires"
    )


class UserRoleResponse(UserRoleAssignment):
    """Schema for user role assignment response."""
    
    id: UUID = Field(
        description="Assignment identifier"
    )
    
    assigned_at: datetime = Field(
        description="When the role was assigned"
    )
    
    assigned_by: UUID = Field(
        description="User who made this assignment"
    )


class PermissionCheck(BaseModel):
    """Schema for checking permissions."""
    
    user_id: UUID = Field(
        description="User to check permissions for"
    )
    
    resource_type: ResourceType = Field(
        title="Resource Type", description="Type of resource to check access to"
    )
    
    action: Action = Field(
        title="Action", description="Action to check permission for"
    )
    
    resource_id: Optional[UUID] = Field(
        default=None,
        title="Resource ID", description="Specific resource to check (null for general permission)"
    )
    
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Context", description="Additional context for permission evaluation"
    )


class PermissionCheckResponse(BaseModel):
    """Schema for permission check response."""
    
    allowed: bool = Field(
        title="Allowed", description="Whether the action is allowed"
    )
    
    reason: Optional[str] = Field(
        default=None,
        title="Reason", description="Reason for the decision (especially if denied)"
    )
    
    matched_permissions: List[Permission] = Field(
        default_factory=list,
        title="Matched Permissions", description="Permissions that granted access"
    )
    
    required_level: Optional[PermissionLevel] = Field(
        default=None,
        title="Required Level", description="Minimum permission level required"
    )


class PermissionSet(BaseModel):
    """Schema for a complete set of permissions."""
    
    user_id: UUID = Field(
        description="User these permissions belong to"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        description="Organization context for permissions"
    )
    
    roles: List[RoleResponse] = Field(
        title="Roles", description="Roles assigned to the user"
    )
    
    direct_permissions: List[Permission] = Field(
        default_factory=list,
        title="Direct Permissions", description="Permissions granted directly to the user"
    )
    
    effective_permissions: List[Permission] = Field(
        title="Effective Permissions", description="All permissions the user has (from roles + direct)"
    )
    
    last_updated: datetime = Field(
        description="When permissions were last calculated"
    )


class BulkRoleAssignment(BaseModel):
    """Schema for bulk role assignments."""
    
    role_id: UUID = Field(
        description="Role to assign"
    )
    
    user_ids: List[UUID] = Field(
        min_items=1,
        max_items=100,
        title="User IDs", description="List of users to assign the role to (max 100)"
    )
    
    scope: Optional[str] = Field(
        default=None,
        title="Scope", description="Scope for all assignments"
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When assignments expire"
    )


class BulkRoleAssignmentResponse(BaseModel):
    """Schema for bulk role assignment response."""
    
    successful_assignments: List[UserRoleResponse] = Field(
        title="Successful Assignments", description="Successfully created role assignments"
    )
    
    failed_assignments: List[Dict[str, Any]] = Field(
        title="Failed Assignments", description="Failed assignments with error details"
    )
    
    total_requested: int = Field(
        title="Total Requested", description="Total number of assignments requested"
    )
    
    total_successful: int = Field(
        title="Total Successful", description="Number of successful assignments"
    )
    
    total_failed: int = Field(
        title="Total Failed", description="Number of failed assignments"
    )
