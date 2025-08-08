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
Security schema module exports.
Provides schemas for API keys, permissions, roles, and two-factor authentication.
"""

# API Key schemas
from .api_keys import (
    APIKeyScope,
    APIKeyStatus,
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeySecret,
    APIKeyListParams,
    APIKeyUsageStats,
    APIKeyRevoke,
)

# Permission and role schemas
from .permissions import (
    ResourceType,
    Action,
    Permission,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    UserRoleAssignment,
    UserRoleResponse,
    PermissionCheck,
    PermissionCheckResponse,
    PermissionSet,
    BulkRoleAssignment,
    BulkRoleAssignmentResponse,
)

# Two-factor authentication schemas
from .two_factor import (
    TwoFactorMethod,
    TwoFactorStatus,
    TwoFactorSetupRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorVerifyResponse,
    TwoFactorMethodResponse,
    TwoFactorDisableRequest,
    TwoFactorBackupCodesResponse,
    TwoFactorStatusResponse,
    TwoFactorRecoveryRequest,
)

__all__ = [
    # API Key schemas
    "APIKeyScope",
    "APIKeyStatus",
    "APIKeyCreate",
    "APIKeyUpdate",
    "APIKeyResponse",
    "APIKeySecret",
    "APIKeyListParams",
    "APIKeyUsageStats",
    "APIKeyRevoke",
    
    # Permission schemas
    "ResourceType",
    "Action",
    "Permission",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "UserRoleAssignment",
    "UserRoleResponse",
    "PermissionCheck",
    "PermissionCheckResponse",
    "PermissionSet",
    "BulkRoleAssignment",
    "BulkRoleAssignmentResponse",
    
    # Two-factor authentication schemas
    "TwoFactorMethod",
    "TwoFactorStatus",
    "TwoFactorSetupRequest",
    "TwoFactorSetupResponse",
    "TwoFactorVerifyRequest",
    "TwoFactorVerifyResponse",
    "TwoFactorMethodResponse",
    "TwoFactorDisableRequest",
    "TwoFactorBackupCodesResponse",
    "TwoFactorStatusResponse",
    "TwoFactorRecoveryRequest",
]
