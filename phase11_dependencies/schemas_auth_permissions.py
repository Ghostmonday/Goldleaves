"""
Permission and role mapping schemas for RBAC enforcement.
Provides schemas for role-based access control and permission management.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
from enum import Enum
from uuid import UUID

from ..base.responses import BaseResponse


def create_field_metadata(**kwargs):
    """Helper to create field metadata for documentation."""
    return kwargs


class Permission(str, Enum):
    """Granular permissions for the system."""
    # User permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    USER_MANAGE = "user:manage"
    USER_SUSPEND = "user:suspend"
    USER_PROMOTE = "user:promote"
    
    # Organization permissions
    ORG_READ = "org:read"
    ORG_WRITE = "org:write"
    ORG_DELETE = "org:delete"
    ORG_MANAGE = "org:manage"
    ORG_BILLING = "org:billing"
    ORG_TRANSFER = "org:transfer"
    
    # Team permissions
    TEAM_READ = "team:read"
    TEAM_WRITE = "team:write"
    TEAM_DELETE = "team:delete"
    TEAM_MANAGE = "team:manage"
    TEAM_MEMBERS = "team:members"
    
    # Document permissions
    DOC_READ = "doc:read"
    DOC_WRITE = "doc:write"
    DOC_DELETE = "doc:delete"
    DOC_SHARE = "doc:share"
    DOC_MANAGE = "doc:manage"
    DOC_VERSIONS = "doc:versions"
    
    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    ADMIN_USERS = "admin:users"
    ADMIN_ORGS = "admin:orgs"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_AUDIT = "admin:audit"
    ADMIN_CONFIG = "admin:config"
    
    # Security permissions
    SECURITY_AUDIT = "security:audit"
    SECURITY_KEYS = "security:keys"
    SECURITY_MFA = "security:mfa"
    SECURITY_SESSIONS = "security:sessions"
    
    # System permissions
    SYSTEM_HEALTH = "system:health"
    SYSTEM_METRICS = "system:metrics"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_BACKUP = "system:backup"
    
    # Special permissions
    SUPER_ADMIN = "super:admin"
    IMPERSONATE = "auth:impersonate"


class RoleType(str, Enum):
    """Types of roles in the system."""
    SYSTEM = "system"  # Built-in system roles
    ORGANIZATION = "organization"  # Organization-specific roles
    CUSTOM = "custom"  # Custom-defined roles


class Role(BaseModel):
    """Role definition with permissions."""
    
    id: UUID = Field(
        description="Unique role identifier"
    )
    
    name: str = Field(
        min_length=1,
        max_length=50,
        description="Role name",
        example="Organization Admin"
    )
    
    code: str = Field(
        min_length=1,
        max_length=50,
        pattern="^[a-z0-9_]+$",
        description="Role code (lowercase, underscores)"
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Role description"
    )
    
    permissions: List[Permission] = Field(
        min_items=1,
        description="Permissions to grant"
    )
    
    inherits_from: Optional[List[str]] = Field(
        default=None,
        description="Role codes to inherit from"
    )
    
    type: RoleType = Field(
        default=RoleType.CUSTOM,
        description="Type of role"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )


class SystemRoles(str, Enum):
    """Built-in system roles."""
    SUPER_ADMIN = "super_admin"
    SYSTEM_ADMIN = "system_admin"
    ORG_OWNER = "org_owner"
    ORG_ADMIN = "org_admin"
    ORG_MEMBER = "org_member"
    TEAM_LEAD = "team_lead"
    TEAM_MEMBER = "team_member"
    GUEST = "guest"
    SUPPORT = "support"
    AUDITOR = "auditor"


# Default permission mappings for system roles
SYSTEM_ROLE_PERMISSIONS: Dict[SystemRoles, List[Permission]] = {
    SystemRoles.SUPER_ADMIN: [Permission.SUPER_ADMIN],  # Has all permissions
    
    SystemRoles.SYSTEM_ADMIN: [
        Permission.ADMIN_ACCESS,
        Permission.ADMIN_USERS,
        Permission.ADMIN_ORGS,
        Permission.ADMIN_SYSTEM,
        Permission.ADMIN_AUDIT,
        Permission.ADMIN_CONFIG,
        Permission.SECURITY_AUDIT,
        Permission.SYSTEM_HEALTH,
        Permission.SYSTEM_METRICS,
        Permission.SYSTEM_LOGS,
    ],
    
    SystemRoles.ORG_OWNER: [
        Permission.ORG_READ,
        Permission.ORG_WRITE,
        Permission.ORG_DELETE,
        Permission.ORG_MANAGE,
        Permission.ORG_BILLING,
        Permission.ORG_TRANSFER,
        Permission.TEAM_READ,
        Permission.TEAM_WRITE,
        Permission.TEAM_DELETE,
        Permission.TEAM_MANAGE,
        Permission.TEAM_MEMBERS,
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.USER_MANAGE,
        Permission.DOC_READ,
        Permission.DOC_WRITE,
        Permission.DOC_DELETE,
        Permission.DOC_SHARE,
        Permission.DOC_MANAGE,
    ],
    
    SystemRoles.ORG_ADMIN: [
        Permission.ORG_READ,
        Permission.ORG_WRITE,
        Permission.ORG_MANAGE,
        Permission.TEAM_READ,
        Permission.TEAM_WRITE,
        Permission.TEAM_MANAGE,
        Permission.TEAM_MEMBERS,
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.USER_MANAGE,
        Permission.DOC_READ,
        Permission.DOC_WRITE,
        Permission.DOC_SHARE,
        Permission.DOC_MANAGE,
    ],
    
    SystemRoles.ORG_MEMBER: [
        Permission.ORG_READ,
        Permission.TEAM_READ,
        Permission.USER_READ,
        Permission.DOC_READ,
        Permission.DOC_WRITE,
        Permission.DOC_SHARE,
    ],
    
    SystemRoles.TEAM_LEAD: [
        Permission.TEAM_READ,
        Permission.TEAM_WRITE,
        Permission.TEAM_MEMBERS,
        Permission.USER_READ,
        Permission.DOC_READ,
        Permission.DOC_WRITE,
        Permission.DOC_SHARE,
        Permission.DOC_MANAGE,
    ],
    
    SystemRoles.TEAM_MEMBER: [
        Permission.TEAM_READ,
        Permission.USER_READ,
        Permission.DOC_READ,
        Permission.DOC_WRITE,
    ],
    
    SystemRoles.GUEST: [
        Permission.USER_READ,
        Permission.DOC_READ,
    ],
    
    SystemRoles.SUPPORT: [
        Permission.USER_READ,
        Permission.ORG_READ,
        Permission.TEAM_READ,
        Permission.DOC_READ,
        Permission.SYSTEM_HEALTH,
        Permission.SECURITY_AUDIT,
    ],
    
    SystemRoles.AUDITOR: [
        Permission.USER_READ,
        Permission.ORG_READ,
        Permission.TEAM_READ,
        Permission.DOC_READ,
        Permission.ADMIN_AUDIT,
        Permission.SECURITY_AUDIT,
        Permission.SYSTEM_LOGS,
    ],
}


class RoleAssignment(BaseModel):
    """Role assignment to a user."""
    
    id: UUID = Field(
        description="Assignment ID"
    )
    
    user_id: UUID = Field(
        description="User receiving the role"
    )
    
    role_id: UUID = Field(
        description="Role being assigned"
    )
    
    role_code: str = Field(
        description="Role code for quick lookup"
    )
    
    scope_type: str = Field(
        default="system",
        pattern="^(system|organization|team|resource)$",
        description="Scope type of the assignment"
    )
    
    scope_id: Optional[UUID] = Field(
        default=None,
        description="ID of the scope (org, team, etc.)"
    )
    
    granted_by: UUID = Field(
        description="User who granted this role"
    )
    
    granted_at: datetime = Field(
        description="When the role was granted"
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When the role assignment expires"
    )
    
    is_active: bool = Field(
        default=True,
        description="Whether the assignment is active"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional assignment metadata"
    )


class PermissionCheck(BaseModel):
    """Request to check user permissions."""
    
    user_id: UUID = Field(
        description="User to check permissions for"
    )
    
    permission: Permission = Field(
        description="Permission to check"
    )
    
    scope_type: Optional[str] = Field(
        default=None,
        description="Scope type to check within"
    )
    
    scope_id: Optional[UUID] = Field(
        default=None,
        description="Scope ID to check within"
    )
    
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for the check"
    )


class PermissionCheckResult(BaseModel):
    """Result of a permission check."""
    
    allowed: bool = Field(
        description="Whether the permission is granted"
    )
    
    user_id: UUID = Field(
        description="User that was checked"
    )
    
    permission: Permission = Field(
        description="Permission that was checked"
    )
    
    granted_by: Optional[List[str]] = Field(
        default=None,
        description="Roles that granted this permission"
    )
    
    scope: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Scope where permission is valid"
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When the permission expires"
    )
    
    conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Any conditions on the permission"
    )


class UserPermissions(BaseModel):
    """Complete permission set for a user."""
    
    user_id: UUID = Field(
        description="User ID"
    )
    
    roles: List[RoleAssignment] = Field(
        description="All role assignments"
    )
    
    direct_permissions: List[Permission] = Field(
        default_factory=list,
        description="Directly assigned permissions"
    )
    
    effective_permissions: Set[Permission] = Field(
        description="All effective permissions (computed)"
    )
    
    permission_sources: Dict[Permission, List[str]] = Field(
        default_factory=dict,
        description="Which roles grant each permission"
    )
    
    scopes: Dict[str, List[UUID]] = Field(
        default_factory=dict,
        description="Scopes where permissions apply"
    )
    
    computed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When permissions were computed"
    )


class PermissionMatrix(BaseModel):
    """Permission matrix showing all roles and their permissions."""
    
    roles: List[Role] = Field(
        description="All roles in the system"
    )
    
    permissions: List[Permission] = Field(
        description="All permissions in the system"
    )
    
    matrix: Dict[str, Dict[str, bool]] = Field(
        description="Role code -> Permission -> has_permission",
        example={
            "org_admin": {
                "user:read": True,
                "user:write": True,
                "user:delete": False
            }
        }
    )
    
    inheritance_map: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Role inheritance relationships"
    )
    
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Matrix statistics"
    )
