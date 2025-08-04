# schemas/auth/permissions.py

"""
Permission and role mapping schemas for RBAC enforcement.
Provides schemas for role-based access control and permission management.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
from enum import Enum
from uuid import UUID

from ..dependencies import create_field_metadata


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


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="New role name"
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="New description"
    )
    
    permissions: Optional[List[Permission]] = Field(
        default=None,
        min_items=1,
        description="New permissions"
    )
    
    inherits_from: Optional[List[str]] = Field(
        default=None,
        description="New inheritance"
    )
    
    is_active: Optional[bool] = Field(
        default=None,
        description="Active status"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="New metadata"
    )


class RoleAssignmentCreate(BaseModel):
    """Schema for assigning a role to a user."""
    
    user_id: UUID = Field(
        description="User to assign role to"
    )
    
    role_id: UUID = Field(
        description="Role to assign"
    )
    
    scope_type: str = Field(
        default="system",
        pattern="^(system|organization|team|resource)$",
        description="Scope type"
    )
    
    scope_id: Optional[UUID] = Field(
        default=None,
        description="Scope ID (if not system)"
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Expiration time"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Assignment metadata"
    )
    
    @validator('scope_id')
    def validate_scope_id(cls, v, values):
        """Ensure scope_id is provided for non-system scopes."""
        if values.get('scope_type') != 'system' and not v:
            raise ValueError("scope_id required for non-system scopes")
        return v


class BulkRoleAssignment(BaseModel):
    """Schema for bulk role assignments."""
    
    user_ids: List[UUID] = Field(
        min_items=1,
        max_items=100,
        description="Users to assign roles to"
    )
    
    role_id: UUID = Field(
        description="Role to assign"
    )
    
    scope_type: str = Field(
        default="system",
        description="Scope type for all assignments"
    )
    
    scope_id: Optional[UUID] = Field(
        default=None,
        description="Scope ID for all assignments"
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Expiration for all assignments"
    )


class PermissionGrant(BaseModel):
    """Direct permission grant to a user."""
    
    user_id: UUID = Field(
        description="User receiving permission"
    )
    
    permission: Permission = Field(
        description="Permission to grant"
    )
    
    scope_type: Optional[str] = Field(
        default=None,
        description="Scope type"
    )
    
    scope_id: Optional[UUID] = Field(
        default=None,
        description="Scope ID"
    )
    
    granted_by: UUID = Field(
        description="User granting permission"
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Expiration time"
    )
    
    reason: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Reason for grant"
    )


class PermissionRevoke(BaseModel):
    """Request to revoke permissions."""
    
    user_id: UUID = Field(
        description="User to revoke from"
    )
    
    permission: Optional[Permission] = Field(
        default=None,
        description="Specific permission to revoke"
    )
    
    role_id: Optional[UUID] = Field(
        default=None,
        description="Specific role to revoke"
    )
    
    scope_type: Optional[str] = Field(
        default=None,
        description="Scope to revoke within"
    )
    
    scope_id: Optional[UUID] = Field(
        default=None,
        description="Scope ID"
    )
    
    reason: str = Field(
        max_length=255,
        description="Reason for revocation"
    )
    
    @validator('permission', 'role_id')
    def validate_target(cls, v, values):
        """Ensure either permission or role_id is provided."""
        if not v and not values.get('role_id') and not values.get('permission'):
            raise ValueError("Either permission or role_id must be provided")
        return v


class AccessPolicy(BaseModel):
    """Access policy for resources."""
    
    id: UUID = Field(
        description="Policy ID"
    )
    
    name: str = Field(
        max_length=100,
        description="Policy name"
    )
    
    resource_type: str = Field(
        description="Type of resource"
    )
    
    resource_id: Optional[UUID] = Field(
        default=None,
        description="Specific resource ID"
    )
    
    required_permissions: List[Permission] = Field(
        min_items=1,
        description="Permissions required for access"
    )
    
    require_all: bool = Field(
        default=True,
        description="Whether all permissions are required"
    )
    
    conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        **create_field_metadata(
            title="Conditions",
            description="Additional access conditions",
            example={"ip_whitelist": ["10.0.0.0/8"], "time_window": "business_hours"}
        )
    )
    
    is_active: bool = Field(
        default=True,
        description="Whether policy is active"
    )
    
    created_at: datetime = Field(
        description="When policy was created"
    )
    
    created_by: UUID = Field(
        description="Who created the policy"
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
    )]+$",
        description="Role code (lowercase, underscores)",
        example="org_admin"
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Role description"
    )
    
    type: RoleType = Field(
        description="Type of role"
    )
    
    permissions: List[Permission] = Field(
        description="Permissions granted by this role"
    )
    
    inherits_from: Optional[List[str]] = Field(
        default=None,
        description="Role codes this role inherits from"
    )
    
    is_active: bool = Field(
        default=True,
        description="Whether the role is active"
    )
    
    created_at: datetime = Field(
        description="When the role was created"
    )
    
    updated_at: datetime = Field(
        description="When the role was last updated"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional role metadata"
    )
    
    @validator('permissions')
    def validate_unique_permissions(cls, v):
        """Ensure permissions are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate permissions not allowed")
        return v


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


class RoleCreate(BaseModel):
    """Schema for creating a new role."""
    
    name: str = Field(
        min_length=1,
        max_length=50,
        description="Role name"
    )
    
    code: str = Field(
        min_length=1,
        max_length=50,
        pattern="^[a-z0-9_






















        # schemas/admin/user_admin.py

"""
Admin user management schemas.
Provides schemas for administrative user operations.
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID

from ..dependencies import (
    create_field_metadata,
    validate_non_empty_string,
    Status
)
from ..auth.permissions import Permission, SystemRoles


class UserAction(str, Enum):
    """Administrative actions on users."""
    PROMOTE = "promote"
    DEMOTE = "demote"
    SUSPEND = "suspend"
    REACTIVATE = "reactivate"
    RESET_PASSWORD = "reset_password"
    RESET_MFA = "reset_mfa"
    FORCE_LOGOUT = "force_logout"
    DELETE = "delete"
    RESTORE = "restore"
    MERGE = "merge"
    TRANSFER_DATA = "transfer_data"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    PENDING = "pending"
    DELETED = "deleted"
    LOCKED = "locked"


class UserFilter(BaseModel):
    """Filter criteria for user queries."""
    
    status: Optional[List[UserStatus]] = Field(
        default=None,
        description="Filter by status"
    )
    
    roles: Optional[List[str]] = Field(
        default=None,
        description="Filter by role codes"
    )
    
    organization_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Filter by organizations"
    )
    
    team_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Filter by teams"
    )
    
    created_after: Optional[datetime] = Field(
        default=None,
        description="Filter users created after"
    )
    
    created_before: Optional[datetime] = Field(
        default=None,
        description="Filter users created before"
    )
    
    last_login_after: Optional[datetime] = Field(
        default=None,
        description="Filter by last login after"
    )
    
    last_login_before: Optional[datetime] = Field(
        default=None,
        description="Filter by last login before"
    )
    
    email_verified: Optional[bool] = Field(
        default=None,
        description="Filter by email verification"
    )
    
    has_mfa: Optional[bool] = Field(
        default=None,
        description="Filter by MFA status"
    )
    
    search_query: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Search in name, email"
    )
    
    include_deleted: bool = Field(
        default=False,
        description="Include deleted users"
    )


class AdminUserResponse(BaseModel):
    """Detailed user information for admins."""
    
    id: UUID = Field(
        description="User ID"
    )
    
    email: EmailStr = Field(
        description="User email"
    )
    
    full_name: Optional[str] = Field(
        default=None,
        description="User's full name"
    )
    
    status: UserStatus = Field(
        description="Account status"
    )
    
    roles: List[Dict[str, Any]] = Field(
        description="User's roles with details"
    )
    
    permissions: List[Permission] = Field(
        description="Effective permissions"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        description="Primary organization"
    )
    
    organization_name: Optional[str] = Field(
        default=None,
        description="Organization name"
    )
    
    team_memberships: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Team memberships"
    )
    
    email_verified: bool = Field(
        description="Email verification status"
    )
    
    mfa_enabled: bool = Field(
        default=False,
        description="MFA status"
    )
    
    last_login: Optional[datetime] = Field(
        default=None,
        description="Last login time"
    )
    
    login_count: int = Field(
        default=0,
        description="Total login count"
    )
    
    failed_login_attempts: int = Field(
        default=0,
        description="Recent failed login attempts"
    )
    
    created_at: datetime = Field(
        description="Account creation time"
    )
    
    updated_at: datetime = Field(
        description="Last update time"
    )
    
    suspended_at: Optional[datetime] = Field(
        default=None,
        description="Suspension time"
    )
    
    suspended_by: Optional[UUID] = Field(
        default=None,
        description="Who suspended the account"
    )
    
    suspension_reason: Optional[str] = Field(
        default=None,
        description="Reason for suspension"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional user metadata"
    )
    
    security_alerts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent security alerts"
    )
    
    api_keys_count: int = Field(
        default=0,
        description="Number of API keys"
    )
    
    active_sessions: int = Field(
        default=0,
        description="Number of active sessions"
    )


class UserPromoteRequest(BaseModel):
    """Request to promote a user."""
    
    user_id: UUID = Field(
        description="User to promote"
    )
    
    new_role: SystemRoles = Field(
        description="New role to assign"
    )
    
    scope_type: str = Field(
        default="system",
        pattern="^(system|organization|team)$",
        description="Scope of the role"
    )
    
    scope_id: Optional[UUID] = Field(
        default=None,
        description="Scope ID if not system"
    )
    
    reason: str = Field(
        min_length=10,
        max_length=500,
        description="Reason for promotion"
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When the promotion expires"
    )
    
    notify_user: bool = Field(
        default=True,
        description="Whether to notify the user"
    )
    
    @validator('new_role')
    def validate_promotion_role(cls, v):
        """Ensure role is appropriate for promotion."""
        if v in [SystemRoles.SUPER_ADMIN]:
            raise ValueError("Cannot promote to super admin via API")
        return v


class UserDemoteRequest(BaseModel):
    """Request to demote a user."""
    
    user_id: UUID = Field(
        description="User to demote"
    )
    
    remove_roles: Optional[List[str]] = Field(
        default=None,
        description="Specific roles to remove"
    )
    
    new_role: Optional[SystemRoles] = Field(
        default=None,
        description="New role to assign after demotion"
    )
    
    reason: str = Field(
        min_length=10,
        max_length=500,
        description="Reason for demotion"
    )
    
    notify_user: bool = Field(
        default=True,
        description="Whether to notify the user"
    )


class UserSuspendRequest(BaseModel):
    """Request to suspend a user."""
    
    user_id: UUID = Field(
        description="User to suspend"
    )
    
    reason: str = Field(
        min_length=10,
        max_length=500,
        description="Reason for suspension"
    )
    
    duration_hours: Optional[int] = Field(
        default=None,
        ge=1,
        le=8760,  # Max 1 year
        description="Suspension duration in hours"
    )
    
    revoke_sessions: bool = Field(
        default=True,
        description="Revoke all active sessions"
    )
    
    revoke_api_keys: bool = Field(
        default=False,
        description="Revoke all API keys"
    )
    
    notify_user: bool = Field(
        default=True,
        description="Send suspension notification"
    )
    
    internal_note: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Internal note (not shown to user)"
    )


class UserReactivateRequest(BaseModel):
    """Request to reactivate a suspended user."""
    
    user_id: UUID = Field(
        description="User to reactivate"
    )
    
    reason: str = Field(
        min_length=10,
        max_length=500,
        description="Reason for reactivation"
    )
    
    restore_roles: bool = Field(
        default=True,
        description="Restore previous roles"
    )
    
    require_password_reset: bool = Field(
        default=False,
        description="Force password reset"
    )
    
    require_mfa_setup: bool = Field(
        default=False,
        description="Force MFA setup"
    )
    
    notify_user: bool = Field(
        default=True,
        description="Send reactivation notification"
    )


class PasswordResetRequest(BaseModel):
    """Admin-initiated password reset."""
    
    user_id: UUID = Field(
        description="User needing password reset"
    )
    
    reason: str = Field(
        max_length=500,
        description="Reason for reset"
    )
    
    temporary_password: Optional[str] = Field(
        default=None,
        description="Temporary password (auto-generated if not provided)"
    )
    
    require_change_on_login: bool = Field(
        default=True,
        description="Force password change on next login"
    )
    
    expire_sessions: bool = Field(
        default=True,
        description="Expire all current sessions"
    )
    
    send_email: bool = Field(
        default=True,
        description="Send reset email to user"
    )


class MFAResetRequest(BaseModel):
    """Request to reset user's MFA."""
    
    user_id: UUID = Field(
        description="User needing MFA reset"
    )
    
    reason: str = Field(
        max_length=500,
        description="Reason for reset"
    )
    
    disable_only: bool = Field(
        default=False,
        description="Only disable MFA, don't reset"
    )
    
    require_setup_on_login: bool = Field(
        default=True,
        description="Force MFA setup on next login"
    )
    
    notify_user: bool = Field(
        default=True,
        description="Notify user of reset"
    )


class UserMergeRequest(BaseModel):
    """Request to merge user accounts."""
    
    primary_user_id: UUID = Field(
        description="Primary user to keep"
    )
    
    merge_user_ids: List[UUID] = Field(
        min_items=1,
        max_items=10,
        description="Users to merge into primary"
    )
    
    merge_strategy: str = Field(
        default="keep_primary",
        pattern="^(keep_primary|keep_newest|keep_most_active|manual)$",
        description="How to handle conflicts"
    )
    
    data_to_merge: List[str] = Field(
        default_factory=lambda: ["documents", "teams", "permissions"],
        description="What data to merge"
    )
    
    reason: str = Field(
        max_length=500,
        description="Reason for merge"
    )
    
    notify_users: bool = Field(
        default=True,
        description="Notify affected users"
    )


class BulkUserAction(BaseModel):
    """Bulk action on multiple users."""
    
    user_ids: List[UUID] = Field(
        min_items=1,
        max_items=100,
        description="Users to act on"
    )
    
    action: UserAction = Field(
        description="Action to perform"
    )
    
    parameters: Dict[str, Any] = Field(
        description="Action-specific parameters"
    )
    
    reason: str = Field(
        max_length=500,
        description="Reason for bulk action"
    )
    
    continue_on_error: bool = Field(
        default=False,
        description="Continue if some actions fail"
    )


class AdminActionResponse(BaseModel):
    """Response for admin actions."""
    
    success: bool = Field(
        description="Whether action succeeded"
    )
    
    action: str = Field(
        description="Action that was performed"
    )
    
    user_id: UUID = Field(
        description="User acted upon"
    )
    
    message: str = Field(
        description="Result message"
    )
    
    changes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="What changed"
    )
    
    warnings: List[str] = Field(
        default_factory=list,
        description="Any warnings"
    )
    
    audit_log_id: Optional[UUID] = Field(
        default=None,
        description="Related audit log entry"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When action occurred"
    )


class BulkActionResponse(BaseModel):
    """Response for bulk actions."""
    
    total_requested: int = Field(
        description="Total users requested"
    )
    
    successful: int = Field(
        description="Successfully processed"
    )
    
    failed: int = Field(
        description="Failed to process"
    )
    
    results: List[AdminActionResponse] = Field(
        description="Individual results"
    )
    
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Error details"
    )
    
    duration_ms: int = Field(
        description="Processing time in milliseconds"
    )


class UserStatistics(BaseModel):
    """User statistics for admin dashboard."""
    
    total_users: int = Field(
        description="Total user count"
    )
    
    active_users: int = Field(
        description="Active user count"
    )
    
    suspended_users: int = Field(
        description="Suspended user count"
    )
    
    deleted_users: int = Field(
        description="Deleted user count"
    )
    
    users_by_status: Dict[str, int] = Field(
        description="Count by status"
    )
    
    users_by_role: Dict[str, int] = Field(
        description="Count by role"
    )
    
    new_users_today: int = Field(
        description="Users created today"
    )
    
    new_users_this_week: int = Field(
        description="Users created this week"
    )
    
    new_users_this_month: int = Field(
        description="Users created this month"
    )
    
    login_stats: Dict[str, Any] = Field(
        description="Login statistics"
    )
    
    mfa_adoption_rate: float = Field(
        description="Percentage with MFA enabled"
    )
    
    email_verification_rate: float = Field(
        description="Percentage with verified email"
    )
    
    average_session_duration: Optional[float] = Field(
        default=None,
        description="Average session duration in minutes"
    )
    
    top_organizations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Organizations with most users"
    )























    # models/audit.py

"""
Audit log model for compliance-grade event tracking.
"""

from sqlalchemy import (
    Boolean, Column, Integer, String, DateTime, ForeignKey, 
    Text, JSON, Index, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from enum import Enum as PyEnum
import uuid

from .dependencies import Base, utcnow, TimestampMixin


class AuditAction(PyEnum):
    """Audit action types matching schema definition."""
    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_SUSPEND = "user.suspend"
    USER_REACTIVATE = "user.reactivate"
    USER_PROMOTE = "user.promote"
    USER_DEMOTE = "user.demote"
    USER_PASSWORD_RESET = "user.password_reset"
    USER_MFA_ENABLE = "user.mfa_enable"
    USER_MFA_DISABLE = "user.mfa_disable"
    
    # Organization actions
    ORG_CREATE = "org.create"
    ORG_UPDATE = "org.update"
    ORG_DELETE = "org.delete"
    ORG_TRANSFER = "org.transfer"
    ORG_BILLING_UPDATE = "org.billing_update"
    
    # Team actions
    TEAM_CREATE = "team.create"
    TEAM_UPDATE = "team.update"
    TEAM_DELETE = "team.delete"
    TEAM_MEMBER_ADD = "team.member_add"
    TEAM_MEMBER_REMOVE = "team.member_remove"
    
    # Document actions
    DOC_CREATE = "doc.create"
    DOC_READ = "doc.read"
    DOC_UPDATE = "doc.update"
    DOC_DELETE = "doc.delete"
    DOC_SHARE = "doc.share"
    DOC_UNSHARE = "doc.unshare"
    DOC_DOWNLOAD = "doc.download"
    DOC_VERSION_CREATE = "doc.version_create"
    DOC_VERSION_RESTORE = "doc.version_restore"
    
    # Permission actions
    PERMISSION_GRANT = "permission.grant"
    PERMISSION_REVOKE = "permission.revoke"
    ROLE_CREATE = "role.create"
    ROLE_UPDATE = "role.update"
    ROLE_DELETE = "role.delete"
    ROLE_ASSIGN = "role.assign"
    ROLE_UNASSIGN = "role.unassign"
    
    # Security actions
    SECURITY_BREACH_ATTEMPT = "security.breach_attempt"
    SECURITY_ACCESS_DENIED = "security.access_denied"
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    SECURITY_API_KEY_CREATE = "security.api_key_create"
    SECURITY_API_KEY_REVOKE = "security.api_key_revoke"
    
    # Admin actions
    ADMIN_CONFIG_UPDATE = "admin.config_update"
    ADMIN_MAINTENANCE_START = "admin.maintenance_start"
    ADMIN_MAINTENANCE_END = "admin.maintenance_end"
    ADMIN_BACKUP_CREATE = "admin.backup_create"
    ADMIN_BACKUP_RESTORE = "admin.backup_restore"
    
    # Data actions
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    DATA_ANONYMIZE = "data.anonymize"
    DATA_RETENTION_APPLY = "data.retention_apply"


class AuditSeverity(PyEnum):
    """Audit event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(PyEnum):
    """Audit event categories."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    USER_MANAGEMENT = "user_management"
    ORGANIZATION = "organization"
    DOCUMENT = "document"
    SECURITY = "security"
    ADMIN = "admin"
    DATA = "data"
    SYSTEM = "system"


class ActorType(PyEnum):
    """Types of actors that can perform actions."""
    USER = "user"
    SYSTEM = "system"
    API = "api"
    ADMIN = "admin"
    SERVICE = "service"


class AuditLog(Base, TimestampMixin):
    """
    Audit log table for compliance and security tracking.
    Stores all significant system events with full context.
    """
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Action details
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)
    category = Column(SQLEnum(AuditCategory), nullable=False, index=True)
    severity = Column(SQLEnum(AuditSeverity), default=AuditSeverity.INFO, nullable=False, index=True)
    
    # Actor information
    actor_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    actor_type = Column(SQLEnum(ActorType), nullable=False, index=True)
    actor_name = Column(String(255), nullable=True)
    actor_email = Column(String(255), nullable=True)
    
    # Target information
    target_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    target_type = Column(String(50), nullable=True, index=True)
    target_name = Column(String(255), nullable=True)
    target_details = Column(JSON, nullable=True)
    
    # Context
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    team_id = Column(Integer, nullable=True, index=True)
    project_id = Column(Integer, nullable=True)
    
    # Request details
    ip_address = Column(String(45), nullable=True)  # Supports IPv6
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(128), nullable=True)
    request_id = Column(String(128), nullable=True, index=True)
    correlation_id = Column(String(128), nullable=True, index=True)
    
    # Event details
    success = Column(Boolean, default=True, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    changes = Column(JSON, nullable=True)  # Before/after values for updates
    metadata = Column(JSON, nullable=True)  # Additional context
    
    # Timestamp (from TimestampMixin provides created_at, updated_at)
    # Additional timestamp for the actual event (may differ from created_at)
    event_timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)
    
    # Retention
    retention_date = Column(DateTime, nullable=True, index=True)
    is_redacted = Column(Boolean, default=False, nullable=False)
    redacted_at = Column(DateTime, nullable=True)
    redacted_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Environment
    environment = Column(String(50), nullable=True)  # production, staging, etc.
    
    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")
    
    # Indexes for common queries
    __table_args__ = (
        # Compound indexes for efficient filtering
        Index('idx_audit_actor_action', 'actor_id', 'action', 'event_timestamp'),
        Index('idx_audit_target_action', 'target_id', 'action', 'event_timestamp'),
        Index('idx_audit_org_category', 'organization_id', 'category', 'event_timestamp'),
        Index('idx_audit_severity_time', 'severity', 'event_timestamp'),
        Index('idx_audit_correlation', 'correlation_id', 'event_timestamp'),
        Index('idx_audit_retention', 'retention_date', 'is_redacted'),
        
        # Index for compliance queries
        Index('idx_audit_compliance', 'organization_id', 'category', 'severity', 'success', 'event_timestamp'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action.value}, actor={self.actor_id}, target={self.target_id})>"
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary with optional sensitive data redaction."""
        data = {
            "id": str(self.id),
            "action": self.action.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "actor_id": str(self.actor_id),
            "actor_type": self.actor_type.value,
            "actor_name": self.actor_name,
            "target_id": str(self.target_id) if self.target_id else None,
            "target_type": self.target_type,
            "target_name": self.target_name,
            "organization_id": self.organization_id,
            "success": self.success,
            "event_timestamp": self.event_timestamp.isoformat() if self.event_timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_sensitive and not self.is_redacted:
            data.update({
                "actor_email": self.actor_email,
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
                "session_id": self.session_id,
                "target_details": self.target_details,
                "changes": self.changes,
                "metadata": self.metadata,
                "error_message": self.error_message,
            })
        elif self.is_redacted:
            data["redacted"] = True
            data["redacted_at"] = self.redacted_at.isoformat() if self.redacted_at else None
        
        return data
    
    def redact(self, redacted_by_id: uuid.UUID):
        """Redact sensitive information from this log entry."""
        self.is_redacted = True
        self.redacted_at = utcnow()
        self.redacted_by = redacted_by_id
        
        # Clear sensitive fields
        self.ip_address = None
        self.user_agent = None
        self.session_id = None
        self.target_details = None
        self.changes = None
        self.metadata = {"redacted": True}
        self.error_message = "REDACTED" if self.error_message else None
    
    @property
    def is_retention_expired(self):
        """Check if this log entry has passed its retention date."""
        if not self.retention_date:
            return False
        return utcnow() > self.retention_date
    
    @staticmethod
    def get_category_for_action(action: AuditAction) -> AuditCategory:
        """Determine the category for a given action."""
        action_str = action.value
        
        if action_str.startswith("user."):
            if action_str in ["user.login", "user.logout"]:
                return AuditCategory.AUTHENTICATION
            return AuditCategory.USER_MANAGEMENT
        elif action_str.startswith("org."):
            return AuditCategory.ORGANIZATION
        elif action_str.startswith("team."):
            return AuditCategory.ORGANIZATION
        elif action_str.startswith("doc."):
            return AuditCategory.DOCUMENT
        elif action_str.startswith("permission.") or action_str.startswith("role."):
            return AuditCategory.AUTHORIZATION
        elif action_str.startswith("security."):
            return AuditCategory.SECURITY
        elif action_str.startswith("admin."):
            return AuditCategory.ADMIN
        elif action_str.startswith("data."):
            return AuditCategory.DATA
        else:
            return AuditCategory.SYSTEM


# Update Organization model to include audit logs relationship
# This would be added to the existing Organization model:
# audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")


















# models/user_role.py

"""
User role and permission models for RBAC.
"""

from sqlalchemy import (
    Boolean, Column, Integer, String, DateTime, ForeignKey, 
    Text, JSON, Index, Enum as SQLEnum, UniqueConstraint, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
from enum import Enum as PyEnum
import uuid

from .dependencies import Base, utcnow, TimestampMixin, SoftDeleteMixin


class Permission(PyEnum):
    """System permissions matching schema definition."""
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


class RoleType(PyEnum):
    """Types of roles in the system."""
    SYSTEM = "system"
    ORGANIZATION = "organization"
    CUSTOM = "custom"


class ScopeType(PyEnum):
    """Types of permission scopes."""
    SYSTEM = "system"
    ORGANIZATION = "organization"
    TEAM = "team"
    RESOURCE = "resource"


# Association tables for many-to-many relationships
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission', String(50), primary_key=True),
    Column('granted_at', DateTime, default=utcnow),
    Column('granted_by', UUID(as_uuid=True), nullable=True)
)

role_inheritance = Table(
    'role_inheritance',
    Base.metadata,
    Column('parent_role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('child_role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=utcnow),
    UniqueConstraint('parent_role_id', 'child_role_id', name='uq_role_inheritance')
)


class Role(Base, TimestampMixin, SoftDeleteMixin):
    """
    Role definition with permissions.
    Supports role inheritance and custom permissions.
    """
    __tablename__ = "roles"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Role identification
    name = Column(String(50), nullable=False)
    code = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Role type and status
    type = Column(SQLEnum(RoleType), default=RoleType.CUSTOM, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system = Column(Boolean, default=False, nullable=False)  # Cannot be modified/deleted
    
    # Organization scope (null for system roles)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Permissions (stored as array for quick access, normalized in association table)
    permissions_array = Column(ARRAY(String), default=[], nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="roles")
    assignments = relationship("RoleAssignment", back_populates="role", cascade="all, delete-orphan")
    
    # Many-to-many relationships
    permissions = relationship(
        "RolePermission",
        cascade="all, delete-orphan",
        back_populates="role"
    )
    
    parent_roles = relationship(
        "Role",
        secondary=role_inheritance,
        primaryjoin=id==role_inheritance.c.child_role_id,
        secondaryjoin=id==role_inheritance.c.parent_role_id,
        backref="child_roles"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_role_org_type', 'organization_id', 'type'),
        Index('idx_role_code_active', 'code', 'is_active'),
        UniqueConstraint('organization_id', 'code', name='uq_role_org_code'),
    )
    
    def __repr__(self):
        return f"<Role(id={self.id}, code={self.code}, type={self.type.value})>"
    
    def add_permission(self, permission: Permission, granted_by: uuid.UUID = None):
        """Add a permission to this role."""
        if permission.value not in self.permissions_array:
            self.permissions_array = self.permissions_array + [permission.value]
    
    def remove_permission(self, permission: Permission):
        """Remove a permission from this role."""
        if permission.value in self.permissions_array:
            self.permissions_array = [p for p in self.permissions_array if p != permission.value]
    
    def get_all_permissions(self, _visited=None):
        """Get all permissions including inherited ones."""
        if _visited is None:
            _visited = set()
        
        # Avoid circular inheritance
        if self.id in _visited:
            return set()
        _visited.add(self.id)
        
        # Start with own permissions
        permissions = set(self.permissions_array)
        
        # Add inherited permissions
        for parent in self.parent_roles:
            if parent.is_active:
                permissions.update(parent.get_all_permissions(_visited))
        
        return permissions


class RolePermission(Base):
    """
    Individual permission grants for roles.
    Allows for detailed permission tracking and conditions.
    """
    __tablename__ = "role_permissions_detailed"
    
    # Composite primary key
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    permission = Column(String(50), primary_key=True)
    
    # Grant details
    granted_at = Column(DateTime, default=utcnow, nullable=False)
    granted_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Conditions (JSON field for flexibility)
    conditions = Column(JSON, nullable=True)  # e.g., {"time_based": true, "hours": "9-17"}
    
    # Expiration
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    role = relationship("Role", back_populates="permissions")
    
    # Indexes
    __table_args__ = (
        Index('idx_role_perm_expires', 'expires_at'),
    )
    
    @property
    def is_expired(self):
        """Check if this permission grant has expired."""
        if not self.expires_at:
            return False
        return utcnow() > self.expires_at


class RoleAssignment(Base, TimestampMixin):
    """
    Assignment of roles to users with scope and expiration.
    """
    __tablename__ = "role_assignments"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Assignment details
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Scope
    scope_type = Column(SQLEnum(ScopeType), default=ScopeType.SYSTEM, nullable=False, index=True)
    scope_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # org_id, team_id, resource_id
    
    # Assignment metadata
    granted_by = Column(UUID(as_uuid=True), nullable=False)
    granted_reason = Column(Text, nullable=True)
    
    # Status and expiration
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(UUID(as_uuid=True), nullable=True)
    revoked_reason = Column(Text, nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="role_assignments")
    role = relationship("Role", back_populates="assignments")
    
    # Indexes for efficient permission checking
    __table_args__ = (
        Index('idx_assignment_user_active', 'user_id', 'is_active'),
        Index('idx_assignment_scope', 'scope_type', 'scope_id', 'is_active'),
        Index('idx_assignment_expires', 'expires_at', 'is_active'),
        UniqueConstraint('user_id', 'role_id', 'scope_type', 'scope_id', name='uq_user_role_scope'),
    )
    
    def __repr__(self):
        return f"<RoleAssignment(user={self.user_id}, role={self.role_id}, scope={self.scope_type.value}:{self.scope_id})>"
    
    @property
    def is_expired(self):
        """Check if this assignment has expired."""
        if not self.expires_at:
            return False
        return utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if this assignment is currently valid."""
        return self.is_active and not self.is_expired and not self.revoked_at
    
    def revoke(self, revoked_by: uuid.UUID, reason: str = None):
        """Revoke this role assignment."""
        self.is_active = False
        self.revoked_at = utcnow()
        self.revoked_by = revoked_by
        self.revoked_reason = reason


class DirectPermissionGrant(Base, TimestampMixin):
    """
    Direct permission grants to users (bypassing roles).
    Used for temporary or special access.
    """
    __tablename__ = "direct_permission_grants"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Grant details
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission = Column(String(50), nullable=False, index=True)
    
    # Scope
    scope_type = Column(SQLEnum(ScopeType), default=ScopeType.SYSTEM, nullable=False)
    scope_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Grant metadata
    granted_by = Column(UUID(as_uuid=True), nullable=False)
    granted_reason = Column(Text, nullable=True)
    
    # Status and expiration
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="direct_permissions")
    
    # Indexes
    __table_args__ = (
        Index('idx_direct_perm_user', 'user_id', 'permission', 'is_active'),
        Index('idx_direct_perm_expires', 'expires_at', 'is_active'),
    )


# Update User model to include these relationships:
# role_assignments = relationship("RoleAssignment", back_populates="user", cascade="all, delete-orphan")
# direct_permissions = relationship("DirectPermissionGrant", back_populates="user", cascade="all, delete-orphan")

# Update Organization model to include:
# roles = relationship("Role", back_populates="organization", cascade="all, delete-orphan")














# services/admin_service.py

"""
Admin service for user management operations.
Handles user promotion, suspension, and other administrative actions.
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from models.user import User, UserStatus, Organization
from models.user_role import Role, RoleAssignment, SystemRoles, Permission, ScopeType
from models.audit import AuditLog, AuditAction, AuditSeverity, ActorType
from schemas.admin.user_admin import (
    UserFilter, AdminUserResponse, UserPromoteRequest, UserDemoteRequest,
    UserSuspendRequest, UserReactivateRequest, PasswordResetRequest,
    MFAResetRequest, UserMergeRequest, BulkUserAction, AdminActionResponse,
    BulkActionResponse, UserStatistics, UserAction
)
from services.audit_log_service import AuditLogService
from services.notification_service import NotificationService
from core.exceptions import NotFoundError, ValidationError, PermissionError
from core.security import get_password_hash
from core.logging import get_logger


logger = get_logger(__name__)


class AdminService:
    """
    Service for administrative user management operations.
    All operations are audited and require appropriate permissions.
    """
    
    @classmethod
    async def get_users(
        cls,
        db: Session,
        admin_user_id: UUID,
        filter_params: UserFilter,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[AdminUserResponse], int]:
        """
        Get users with detailed information for admin view.
        
        Args:
            db: Database session
            admin_user_id: Admin performing the query
            filter_params: Filter criteria
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            Tuple of (users, total_count)
        """
        # Build base query
        query = db.query(User)
        
        # Apply filters
        if filter_params.status:
            query = query.filter(User.status.in_(filter_params.status))
        
        if filter_params.organization_ids:
            query = query.filter(User.organization_id.in_(filter_params.organization_ids))
        
        if filter_params.created_after:
            query = query.filter(User.created_at >= filter_params.created_after)
        
        if filter_params.created_before:
            query = query.filter(User.created_at <= filter_params.created_before)
        
        if filter_params.last_login_after:
            query = query.filter(User.last_login >= filter_params.last_login_after)
        
        if filter_params.last_login_before:
            query = query.filter(User.last_login <= filter_params.last_login_before)
        
        if filter_params.email_verified is not None:
            query = query.filter(User.email_verified == filter_params.email_verified)
        
        if filter_params.search_query:
            search_term = f"%{filter_params.search_query}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term)
                )
            )
        
        if not filter_params.include_deleted:
            query = query.filter(User.is_deleted == False)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.offset(skip).limit(limit).all()
        
        # Convert to admin response format
        admin_users = []
        for user in users:
            admin_user = await cls._build_admin_user_response(db, user)
            admin_users.append(admin_user)
        
        # Log the query
        await AuditLogService.log_action(
            db=db,
            action=AuditAction.USER_READ,
            actor_id=admin_user_id,
            actor_type=ActorType.ADMIN,
            metadata={
                "filter": filter_params.dict(exclude_none=True),
                "result_count": len(admin_users),
                "total_count": total
            }
        )
        
        return admin_users, total
    
    @classmethod
    async def promote_user(
        cls,
        db: Session,
        admin_user_id: UUID,
        request: UserPromoteRequest
    ) -> AdminActionResponse:
        """
        Promote a user to a higher role.
        
        Args:
            db: Database session
            admin_user_id: Admin performing the promotion
            request: Promotion request details
            
        Returns:
            Action response
        """
        # Get target user
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise NotFoundError(f"User {request.user_id} not found")
        
        # Validate promotion
        if user.id == admin_user_id:
            raise ValidationError("Cannot promote yourself")
        
        # Get or create the role
        role = db.query(Role).filter(Role.code == request.new_role.value).first()
        if not role:
            raise ValidationError(f"Role {request.new_role.value} not configured")
        
        # Check if user already has this role
        existing = db.query(RoleAssignment).filter(
            and_(
                RoleAssignment.user_id == user.id,
                RoleAssignment.role_id == role.id,
                RoleAssignment.scope_type == request.scope_type,
                RoleAssignment.scope_id == request.scope_id,
                RoleAssignment.is_active == True
            )
        ).first()
        
        if existing and existing.is_valid:
            raise ValidationError("User already has this role")
        
        # Create role assignment
        assignment = RoleAssignment(
            user_id=user.id,
            role_id=role.id,
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            granted_by=admin_user_id,
            granted_reason=request.reason,
            expires_at=request.expires_at
        )
        db.add(assignment)
        
        # Log the action
        audit_log = await AuditLogService.log_action(
            db=db,
            action=AuditAction.USER_PROMOTE,
            actor_id=admin_user_id,
            actor_type=ActorType.ADMIN,
            target_id=user.id,
            target_type="user",
            changes={
                "role": request.new_role.value,
                "scope": request.scope_type,
                "expires_at": request.expires_at.isoformat() if request.expires_at else None
            },
            metadata={"reason": request.reason}
        )
        
        # Send notification
        if request.notify_user:
            await NotificationService.send_user_notification(
                db=db,
                user_id=user.id,
                template="role_demotion",
                context={
                    "removed_roles": changes["removed_roles"],
                    "new_role": changes["new_role"],
                    "reason": request.reason
                }
            )
        
        db.commit()
        
        return AdminActionResponse(
            success=True,
            action="demote",
            user_id=user.id,
            message=f"User demoted successfully",
            changes=changes,
            audit_log_id=audit_log.id
        )
    
    @classmethod
    async def suspend_user(
        cls,
        db: Session,
        admin_user_id: UUID,
        request: UserSuspendRequest
    ) -> AdminActionResponse:
        """
        Suspend a user account.
        
        Args:
            db: Database session
            admin_user_id: Admin performing the suspension
            request: Suspension request details
            
        Returns:
            Action response
        """
        # Get target user
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise NotFoundError(f"User {request.user_id} not found")
        
        # Validate suspension
        if user.id == admin_user_id:
            raise ValidationError("Cannot suspend yourself")
        
        if user.status == UserStatus.SUSPENDED:
            raise ValidationError("User is already suspended")
        
        # Store previous status for potential restoration
        previous_status = user.status
        
        # Suspend the user
        user.status = UserStatus.SUSPENDED
        user.is_active = False
        user.suspended_at = datetime.utcnow()
        user.suspended_by = admin_user_id
        user.suspension_reason = request.reason
        
        # Calculate suspension end time
        suspension_end = None
        if request.duration_hours:
            suspension_end = datetime.utcnow() + timedelta(hours=request.duration_hours)
            user.suspension_expires_at = suspension_end
        
        changes = {
            "previous_status": previous_status.value,
            "new_status": UserStatus.SUSPENDED.value,
            "suspension_end": suspension_end.isoformat() if suspension_end else None
        }
        
        # Revoke sessions if requested
        if request.revoke_sessions:
            # This would call a session management service
            revoked_count = await cls._revoke_user_sessions(db, user.id)
            changes["revoked_sessions"] = revoked_count
        
        # Revoke API keys if requested
        if request.revoke_api_keys:
            # This would call an API key management service
            revoked_keys = await cls._revoke_user_api_keys(db, user.id)
            changes["revoked_api_keys"] = revoked_keys
        
        # Store internal note if provided
        if request.internal_note:
            user.metadata = user.metadata or {}
            user.metadata["suspension_note"] = request.internal_note
        
        # Log the action
        audit_log = await AuditLogService.log_action(
            db=db,
            action=AuditAction.USER_SUSPEND,
            actor_id=admin_user_id,
            actor_type=ActorType.ADMIN,
            target_id=user.id,
            target_type="user",
            severity=AuditSeverity.WARNING,
            changes=changes,
            metadata={
                "reason": request.reason,
                "internal_note": request.internal_note,
                "duration_hours": request.duration_hours
            }
        )
        
        # Send notification
        if request.notify_user:
            await NotificationService.send_user_notification(
                db=db,
                user_id=user.id,
                template="account_suspended",
                context={
                    "reason": request.reason,
                    "suspension_end": suspension_end,
                    "contact_support": True
                }
            )
        
        db.commit()
        
        return AdminActionResponse(
            success=True,
            action="suspend",
            user_id=user.id,
            message=f"User suspended{'for ' + str(request.duration_hours) + ' hours' if request.duration_hours else ' indefinitely'}",
            changes=changes,
            audit_log_id=audit_log.id
        )
    
    @classmethod
    async def reactivate_user(
        cls,
        db: Session,
        admin_user_id: UUID,
        request: UserReactivateRequest
    ) -> AdminActionResponse:
        """
        Reactivate a suspended user account.
        
        Args:
            db: Database session
            admin_user_id: Admin performing the reactivation
            request: Reactivation request details
            
        Returns:
            Action response
        """
        # Get target user
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise NotFoundError(f"User {request.user_id} not found")
        
        # Validate reactivation
        if user.status != UserStatus.SUSPENDED:
            raise ValidationError("User is not suspended")
        
        # Reactivate the user
        user.status = UserStatus.ACTIVE
        user.is_active = True
        user.suspended_at = None
        user.suspended_by = None
        user.suspension_reason = None
        user.suspension_expires_at = None
        
        changes = {
            "previous_status": UserStatus.SUSPENDED.value,
            "new_status": UserStatus.ACTIVE.value,
            "restored_roles": []
        }
        
        # Restore roles if requested
        if request.restore_roles:
            # Reactivate previously revoked role assignments
            restored = db.query(RoleAssignment).filter(
                and_(
                    RoleAssignment.user_id == user.id,
                    RoleAssignment.revoked_reason.like("%suspension%"),
                    RoleAssignment.revoked_at != None
                )
            ).all()
            
            for assignment in restored:
                assignment.is_active = True
                assignment.revoked_at = None
                assignment.revoked_by = None
                assignment.revoked_reason = None
                changes["restored_roles"].append(assignment.role.code)
        
        # Set security requirements
        if request.require_password_reset:
            user.force_password_reset = True
            changes["require_password_reset"] = True
        
        if request.require_mfa_setup:
            user.force_mfa_setup = True
            changes["require_mfa_setup"] = True
        
        # Log the action
        audit_log = await AuditLogService.log_action(
            db=db,
            action=AuditAction.USER_REACTIVATE,
            actor_id=admin_user_id,
            actor_type=ActorType.ADMIN,
            target_id=user.id,
            target_type="user",
            changes=changes,
            metadata={"reason": request.reason}
        )
        
        # Send notification
        if request.notify_user:
            await NotificationService.send_user_notification(
                db=db,
                user_id=user.id,
                template="account_reactivated",
                context={
                    "reason": request.reason,
                    "require_password_reset": request.require_password_reset,
                    "require_mfa_setup": request.require_mfa_setup
                }
            )
        
        db.commit()
        
        return AdminActionResponse(
            success=True,
            action="reactivate",
            user_id=user.id,
            message="User account reactivated",
            changes=changes,
            audit_log_id=audit_log.id
        )
    
    @classmethod
    async def reset_user_password(
        cls,
        db: Session,
        admin_user_id: UUID,
        request: PasswordResetRequest
    ) -> AdminActionResponse:
        """
        Reset a user's password administratively.
        
        Args:
            db: Database session
            admin_user_id: Admin performing the reset
            request: Password reset request details
            
        Returns:
            Action response
        """
        # Get target user
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise NotFoundError(f"User {request.user_id} not found")
        
        # Generate temporary password if not provided
        temp_password = request.temporary_password
        if not temp_password:
            temp_password = cls._generate_temporary_password()
        
        # Hash and set the password
        user.hashed_password = get_password_hash(temp_password)
        
        # Set password reset requirements
        if request.require_change_on_login:
            user.force_password_reset = True
        
        # Expire sessions if requested
        sessions_expired = 0
        if request.expire_sessions:
            sessions_expired = await cls._revoke_user_sessions(db, user.id)
        
        # Log the action (without the actual password)
        audit_log = await AuditLogService.log_action(
            db=db,
            action=AuditAction.USER_PASSWORD_RESET,
            actor_id=admin_user_id,
            actor_type=ActorType.ADMIN,
            target_id=user.id,
            target_type="user",
            severity=AuditSeverity.WARNING,
            metadata={
                "reason": request.reason,
                "require_change": request.require_change_on_login,
                "sessions_expired": sessions_expired
            }
        )
        
        # Send email if requested
        if request.send_email:
            await NotificationService.send_user_notification(
                db=db,
                user_id=user.id,
                template="password_reset_admin",
                context={
                    "temporary_password": temp_password,
                    "reason": request.reason,
                    "require_change": request.require_change_on_login
                }
            )
        
        db.commit()
        
        return AdminActionResponse(
            success=True,
            action="reset_password",
            user_id=user.id,
            message="Password reset successfully",
            changes={
                "sessions_expired": sessions_expired,
                "email_sent": request.send_email
            },
            warnings=["Temporary password provided to user"] if request.send_email else [],
            audit_log_id=audit_log.id
        )
    
    @classmethod
    async def reset_user_mfa(
        cls,
        db: Session,
        admin_user_id: UUID,
        request: MFAResetRequest
    ) -> AdminActionResponse:
        """
        Reset a user's MFA settings.
        
        Args:
            db: Database session
            admin_user_id: Admin performing the reset
            request: MFA reset request details
            
        Returns:
            Action response
        """
        # Get target user
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise NotFoundError(f"User {request.user_id} not found")
        
        changes = {}
        
        # Reset MFA settings
        if request.disable_only:
            user.mfa_enabled = False
            user.mfa_secret = None
            changes["mfa_disabled"] = True
        else:
            # Full reset - clear all MFA data
            user.mfa_enabled = False
            user.mfa_secret = None
            user.mfa_backup_codes = None
            user.mfa_last_used = None
            changes["mfa_reset"] = True
        
        # Set requirement for next login
        if request.require_setup_on_login:
            user.force_mfa_setup = True
            changes["require_setup"] = True
        
        # Log the action
        audit_log = await AuditLogService.log_action(
            db=db,
            action=AuditAction.USER_MFA_DISABLE if request.disable_only else AuditAction.USER_MFA_ENABLE,
            actor_id=admin_user_id,
            actor_type=ActorType.ADMIN,
            target_id=user.id,
            target_type="user",
            severity=AuditSeverity.WARNING,
            metadata={"reason": request.reason}
        )
        
        # Send notification
        if request.notify_user:
            await NotificationService.send_user_notification(
                db=db,
                user_id=user.id,
                template="mfa_reset",
                context={
                    "reason": request.reason,
                    "require_setup": request.require_setup_on_login
                }
            )
        
        db.commit()
        
        return AdminActionResponse(
            success=True,
            action="reset_mfa",
            user_id=user.id,
            message="MFA settings reset successfully",
            changes=changes,
            audit_log_id=audit_log.id
        )
    
    @classmethod
    async def get_user_statistics(
        cls,
        db: Session,
        admin_user_id: UUID,
        organization_id: Optional[int] = None
    ) -> UserStatistics:
        """
        Get comprehensive user statistics for admin dashboard.
        
        Args:
            db: Database session
            admin_user_id: Admin requesting statistics
            organization_id: Optional organization filter
            
        Returns:
            User statistics
        """
        # Base query
        query = db.query(User)
        if organization_id:
            query = query.filter(User.organization_id == organization_id)
        
        # Get counts by status
        total_users = query.count()
        active_users = query.filter(User.status == UserStatus.ACTIVE).count()
        suspended_users = query.filter(User.status == UserStatus.SUSPENDED).count()
        deleted_users = query.filter(User.is_deleted == True).count()
        
        # Status breakdown
        users_by_status = {}
        for status in UserStatus:
            count = query.filter(User.status == status).count()
            users_by_status[status.value] = count
        
        # Role breakdown
        users_by_role = db.query(
            Role.code, func.count(RoleAssignment.user_id).label('count')
        ).join(
            RoleAssignment, Role.id == RoleAssignment.role_id
        ).filter(
            RoleAssignment.is_active == True
        ).group_by(Role.code).all()
        
        users_by_role_dict = {role: count for role, count in users_by_role}
        
        # Time-based statistics
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)
        
        new_users_today = query.filter(User.created_at >= today_start).count()
        new_users_this_week = query.filter(User.created_at >= week_start).count()
        new_users_this_month = query.filter(User.created_at >= month_start).count()
        
        # MFA and email verification rates
        mfa_enabled_count = query.filter(User.mfa_enabled == True).count()
        email_verified_count = query.filter(User.email_verified == True).count()
        
        mfa_adoption_rate = (mfa_enabled_count / total_users * 100) if total_users > 0 else 0
        email_verification_rate = (email_verified_count / total_users * 100) if total_users > 0 else 0
        
        # Top organizations
        top_orgs = []
        if not organization_id:
            org_stats = db.query(
                Organization.id,
                Organization.name,
                func.count(User.id).label('user_count')
            ).join(
                User, Organization.id == User.organization_id
            ).group_by(
                Organization.id, Organization.name
            ).order_by(
                func.count(User.id).desc()
            ).limit(10).all()
            
            top_orgs = [
                {"id": org_id, "name": name, "user_count": count}
                for org_id, name, count in org_stats
            ]
        
        return UserStatistics(
            total_users=total_users,
            active_users=active_users,
            suspended_users=suspended_users,
            deleted_users=deleted_users,
            users_by_status=users_by_status,
            users_by_role=users_by_role_dict,
            new_users_today=new_users_today,
            new_users_this_week=new_users_this_week,
            new_users_this_month=new_users_this_month,
            login_stats={
                "active_today": query.filter(User.last_login >= today_start).count(),
                "active_this_week": query.filter(User.last_login >= week_start).count(),
                "active_this_month": query.filter(User.last_login >= month_start).count()
            },
            mfa_adoption_rate=round(mfa_adoption_rate, 2),
            email_verification_rate=round(email_verification_rate, 2),
            top_organizations=top_orgs
        )
    
    @classmethod
    async def _build_admin_user_response(cls, db: Session, user: User) -> AdminUserResponse:
        """Build detailed admin user response."""
        # Get user's roles
        role_assignments = db.query(RoleAssignment).filter(
            and_(
                RoleAssignment.user_id == user.id,
                RoleAssignment.is_active == True
            )
        ).all()
        
        roles = []
        permissions = set()
        
        for assignment in role_assignments:
            if assignment.is_valid:
                roles.append({
                    "id": str(assignment.role.id),
                    "code": assignment.role.code,
                    "name": assignment.role.name,
                    "scope": assignment.scope_type.value,
                    "scope_id": str(assignment.scope_id) if assignment.scope_id else None,
                    "expires_at": assignment.expires_at
                })
                permissions.update(assignment.role.get_all_permissions())
        
        # Get team memberships (simplified for now)
        team_memberships = []
        
        # Get security alerts (simplified for now)
        security_alerts = []
        
        return AdminUserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            status=user.status,
            roles=roles,
            permissions=list(permissions),
            organization_id=user.organization_id,
            organization_name=user.organization.name if user.organization else None,
            team_memberships=team_memberships,
            email_verified=user.email_verified,
            mfa_enabled=user.mfa_enabled,
            last_login=user.last_login,
            login_count=user.login_count,
            failed_login_attempts=0,  # Would come from security service
            created_at=user.created_at,
            updated_at=user.updated_at,
            suspended_at=user.suspended_at,
            suspended_by=user.suspended_by,
            suspension_reason=user.suspension_reason,
            metadata=user.metadata or {},
            security_alerts=security_alerts,
            api_keys_count=0,  # Would come from API key service
            active_sessions=0  # Would come from session service
        )
    
    @classmethod
    async def _revoke_user_sessions(cls, db: Session, user_id: UUID) -> int:
        """Revoke all active sessions for a user."""
        # This would integrate with session management
        # For now, return a placeholder
        return 0
    
    @classmethod
    async def _revoke_user_api_keys(cls, db: Session, user_id: UUID) -> int:
        """Revoke all API keys for a user."""
        # This would integrate with API key management
        # For now, return a placeholder
        return 0
    
    @classmethod
    def _generate_temporary_password(cls) -> str:
        """Generate a secure temporary password."""
        # Generate a password with letters, digits, and special characters
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(16))
        return passwordreason": request.reason}
        )
        
        # Send notification
        if request.notify_user:
            await NotificationService.send_user_notification(
                db=db,
                user_id=user.id,
                template="role_promotion",
                context={
                    "role_name": role.name,
                    "reason": request.reason,
                    "expires_at": request.expires_at
                }
            )
        
        db.commit()
        
        return AdminActionResponse(
            success=True,
            action="promote",
            user_id=user.id,
            message=f"User promoted to {role.name}",
            changes={"role_id": str(assignment.id)},
            audit_log_id=audit_log.id
        )
    
    @classmethod
    async def demote_user(
        cls,
        db: Session,
        admin_user_id: UUID,
        request: UserDemoteRequest
    ) -> AdminActionResponse:
        """
        Demote a user by removing roles.
        
        Args:
            db: Database session
            admin_user_id: Admin performing the demotion
            request: Demotion request details
            
        Returns:
            Action response
        """
        # Get target user
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise NotFoundError(f"User {request.user_id} not found")
        
        # Validate demotion
        if user.id == admin_user_id:
            raise ValidationError("Cannot demote yourself")
        
        changes = {"removed_roles": [], "new_role": None}
        
        # Remove specified roles
        if request.remove_roles:
            assignments = db.query(RoleAssignment).join(Role).filter(
                and_(
                    RoleAssignment.user_id == user.id,
                    Role.code.in_(request.remove_roles),
                    RoleAssignment.is_active == True
                )
            ).all()
            
            for assignment in assignments:
                assignment.revoke(admin_user_id, request.reason)
                changes["removed_roles"].append(assignment.role.code)
        
        # Assign new role if specified
        if request.new_role:
            role = db.query(Role).filter(Role.code == request.new_role.value).first()
            if role:
                new_assignment = RoleAssignment(
                    user_id=user.id,
                    role_id=role.id,
                    scope_type=ScopeType.SYSTEM,
                    granted_by=admin_user_id,
                    granted_reason=f"Demotion: {request.reason}"
                )
                db.add(new_assignment)
                changes["new_role"] = role.code
        
        # Log the action
        audit_log = await AuditLogService.log_action(
            db=db,
            action=AuditAction.USER_DEMOTE,
            actor_id=admin_user_id,
            actor_type=ActorType.ADMIN,
            target_id=user.id,
            target_type="user",
            changes=changes,
            metadata={"