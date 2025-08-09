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
API key management schemas for authentication and authorization.
Provides schemas for creating, managing, and validating API keys.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, SecretStr, validator

from ..dependencies import create_field_metadata, validate_non_empty_string


class APIKeyScope(str, Enum):
    """Available API key scopes/permissions."""
    
    # Document permissions
    READ_DOCUMENTS = "documents:read"
    WRITE_DOCUMENTS = "documents:write"
    DELETE_DOCUMENTS = "documents:delete"
    MANAGE_DOCUMENTS = "documents:manage"
    
    # Organization permissions
    READ_ORGANIZATION = "organization:read"
    WRITE_ORGANIZATION = "organization:write"
    MANAGE_MEMBERS = "organization:members"
    MANAGE_TEAMS = "organization:teams"
    
    # User permissions
    READ_USERS = "users:read"
    WRITE_USERS = "users:write"
    
    # Webhook permissions
    READ_WEBHOOKS = "webhooks:read"
    WRITE_WEBHOOKS = "webhooks:write"
    
    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_FULL = "admin:*"


class APIKeyStatus(str, Enum):
    """API key status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"


class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    
    name: str = Field(
        min_length=1, max_length=100,
        title="API Key Name", description="Human-readable name for the API key", example="Production Integration Key"
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Description", description="Optional description of the API key's purpose", example="API key for production webhook integrations"
    )
    
    scopes: List[APIKeyScope] = Field(
        min_items=1,
        **create_field_metadata(
            title="Scopes",
            description="List of permissions granted to this API key",
            example=["documents:read", "documents:write"]
        )
    )
    
    expires_in_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        **create_field_metadata(
            title="Expiration Days",
            description="Number of days until the key expires (max 365)",
            example=90
        )
    )
    
    rate_limit: Optional[int] = Field(
        default=1000,
        ge=1,
        le=10000,
        **create_field_metadata(
            title="Rate Limit",
            description="Requests per hour allowed for this key",
            example=1000
        )
    )
    
    ip_whitelist: Optional[List[str]] = Field(
        default=None,
        **create_field_metadata(
            title="IP Whitelist",
            description="List of IP addresses allowed to use this key",
            example=["192.168.1.1", "10.0.0.0/24"]
        )
    )
    
    @validator('name')
    def validate_name(cls, v):
        """Validate API key name."""
        return validate_non_empty_string(v)
    
    @validator('scopes')
    def validate_scopes(cls, v):
        """Validate API key scopes."""
        if not v:
            raise ValueError("At least one scope is required")
        
        # Check for conflicting scopes
        if APIKeyScope.ADMIN_FULL in v and len(v) > 1:
            raise ValueError("admin:* scope cannot be combined with other scopes")
        
        return v
    
    @validator('ip_whitelist')
    def validate_ip_whitelist(cls, v):
        """Validate IP whitelist format."""
        if v is None:
            return v
        
        import ipaddress
        for ip in v:
            try:
                # Try to parse as IP address or network
                ipaddress.ip_network(ip, strict=False)
            except ValueError:
                raise ValueError(f"Invalid IP address or network: {ip}")
        
        return v


class APIKeyUpdate(BaseModel):
    """Schema for updating an existing API key."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=1, max_length=100
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=500
    )
    
    status: Optional[APIKeyStatus] = Field(
        default=None,
        title="Status", description="New status for the API key"
    )
    
    rate_limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=10000
    )
    
    ip_whitelist: Optional[List[str]] = Field(
        default=None
    )
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            return validate_non_empty_string(v)
        return v


class APIKeyResponse(BaseModel):
    """Schema for API key response (without secret)."""
    
    id: UUID = Field(
        description="Unique API key identifier"
    )
    
    name: str = Field(
        title="Name", description="API key name"
    )
    
    description: Optional[str] = Field(
        title="Description", description="API key description"
    )
    
    key_prefix: str = Field(
        title="Key Prefix", description="First 8 characters of the API key for identification", example="gk_live_"
    )
    
    scopes: List[APIKeyScope] = Field(
        title="Scopes", description="Permissions granted to this API key"
    )
    
    status: APIKeyStatus = Field(
        title="Status", description="Current status of the API key"
    )
    
    rate_limit: int = Field(
        title="Rate Limit", description="Requests per hour allowed"
    )
    
    ip_whitelist: Optional[List[str]] = Field(
        title="IP Whitelist", description="Allowed IP addresses"
    )
    
    usage_count: int = Field(
        default=0,
        title="Usage Count", description="Total number of requests made with this key"
    )
    
    last_used_at: Optional[datetime] = Field(
        default=None,
        description="Last time the key was used"
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When the key expires"
    )
    
    created_at: datetime = Field(
        description="When the key was created"
    )
    
    updated_at: datetime = Field(
        description="When the key was last updated"
    )
    
    created_by: UUID = Field(
        description="User who created this key"
    )


class APIKeySecret(APIKeyResponse):
    """Schema for API key response with secret (only returned on creation)."""
    
    key: SecretStr = Field(
        title="API Key", description="The actual API key secret (only shown once)", example="gk_live_1234567890abcdef1234567890abcdef"
    )
    
    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }


class APIKeyListParams(BaseModel):
    """Parameters for listing API keys."""
    
    status: Optional[APIKeyStatus] = Field(
        default=None,
        title="Status Filter", description="Filter by key status"
    )
    
    scope: Optional[APIKeyScope] = Field(
        default=None,
        title="Scope Filter", description="Filter by scope"
    )
    
    search: Optional[str] = Field(
        default=None,
        max_length=100,
        title="Search", description="Search in key names and descriptions"
    )
    
    created_after: Optional[datetime] = Field(
        default=None,
        title="Created After", description="Filter keys created after this date"
    )


class APIKeyUsageStats(BaseModel):
    """API key usage statistics."""
    
    total_requests: int = Field(
        title="Total Requests", description="Total number of requests made"
    )
    
    requests_last_24h: int = Field(
        title="Requests Last 24h", description="Requests made in the last 24 hours"
    )
    
    requests_last_7d: int = Field(
        title="Requests Last 7 Days", description="Requests made in the last 7 days"
    )
    
    avg_requests_per_day: float = Field(
        title="Average Requests Per Day", description="Average daily request count"
    )
    
    last_request_at: Optional[datetime] = Field(
        description="Timestamp of last request"
    )
    
    most_used_endpoint: Optional[str] = Field(
        title="Most Used Endpoint", description="The API endpoint used most frequently"
    )


class APIKeyRevoke(BaseModel):
    """Schema for revoking an API key."""
    
    reason: Optional[str] = Field(
        default=None,
        max_length=200,
        title="Revocation Reason", description="Optional reason for revoking the key", example="Security concern - key may be compromised"
    )
