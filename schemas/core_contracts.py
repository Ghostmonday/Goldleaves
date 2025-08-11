
# ---- contract.py ----
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


from typing import Dict, List, Type, Any
from pydantic import BaseModel

class SchemaContract(BaseModel):
    version: str = "4.0.0"
    capabilities: List[str] = [
        "organization_schemas",
        "security_schemas",
        "document_schemas",
        "audit_schemas",
        "webhook_schemas",
        "pagination_support"
    ]

    exports: Dict[str, Type[BaseModel]] = {
        "OrganizationCreate": "organization.core.OrganizationCreate",
        "OrganizationResponse": "organization.core.OrganizationResponse",
        "TeamCreate": "organization.teams.TeamCreate",
        "MemberInvite": "organization.invites.MemberInvite",

        "APIKeyCreate": "security.api_keys.APIKeyCreate",
        "TwoFactorSetup": "security.two_factor.TwoFactorSetup",
        "PermissionSet": "security.permissions.PermissionSet",

        "DocumentVersion": "document.versioning.DocumentVersion",
        "ShareLinkCreate": "document.sharing.ShareLinkCreate",
        "CommentCreate": "document.comments.CommentCreate",

        "AuditLogEntry": "audit.logs.AuditLogEntry",
        "AuditFilter": "audit.logs.AuditFilter",

        "WebhookCreate": "webhooks.config.WebhookCreate",
        "WebhookPayload": "webhooks.payloads.WebhookPayload"
    }

# ---- dependencies.py ----
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
Shared validation utilities and dependencies for all schema modules.
Provides reusable validators, field types, and utility functions.
"""

from typing import Optional, Any, List, Dict
from enum import Enum
import re
from pydantic import Field


# === SHARED FIELD TYPES ===

def non_empty_string(min_length: int = 1, max_length: int = 255) -> Field:
    """Create a non-empty string field with length constraints."""
    return Field(
        min_length=min_length, 
        max_length=max_length,
        description=f"Non-empty string ({min_length}-{max_length} chars)"
    )

def optional_string(max_length: int = 255) -> Field:
    """Create an optional string field with max length."""
    return Field(
        default=None,
        max_length=max_length,
        description=f"Optional string (max {max_length} chars)"
    )

def email_field() -> Field:
    """Create an email field with validation."""
    return Field(
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        description="Valid email address"
    )

def uuid_field(description: str = "UUID identifier") -> Field:
    """Create a UUID field."""
    return Field(description=description)

def timestamp_field(description: str = "Timestamp") -> Field:
    """Create a timestamp field."""
    return Field(description=description)


# === SHARED ENUMS ===

class Status(str, Enum):
    """Generic status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class Priority(str, Enum):
    """Priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class PermissionLevel(str, Enum):
    """Permission levels."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


# === SHARED VALIDATORS ===

def validate_non_empty_string(value: Optional[str]) -> Optional[str]:
    """Validate that string is not empty or whitespace-only."""
    if value is None:
        return value
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError("String cannot be empty or whitespace-only")

def validate_slug(value: str) -> str:
    """Validate slug format (lowercase letters, numbers, hyphens)."""
    if not re.match(r'^[a-z0-9-]+$', value):
        raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
    if value.startswith('-') or value.endswith('-'):
        raise ValueError("Slug cannot start or end with hyphen")
    return value

def validate_password_strength(value: str) -> str:
    """Validate password meets security requirements."""
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r'[A-Z]', value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r'\d', value):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValueError("Password must contain at least one special character")
    return value

def validate_phone_number(value: Optional[str]) -> Optional[str]:
    """Validate phone number format."""
    if value is None:
        return value
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', value)
    if len(digits_only) < 10 or len(digits_only) > 15:
        raise ValueError("Phone number must be 10-15 digits")
    return value

def validate_url(value: Optional[str]) -> Optional[str]:
    """Validate URL format."""
    if value is None:
        return value
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if not url_pattern.match(value):
        raise ValueError("Invalid URL format")
    return value


# === UTILITY FUNCTIONS ===

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace dangerous characters
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple consecutive underscores
    safe_filename = re.sub(r'_+', '_', safe_filename)
    # Remove leading/trailing underscores and dots
    safe_filename = safe_filename.strip('_.')
    
    if not safe_filename:
        return "unnamed_file"
    
    return safe_filename

def generate_unique_slug(base_slug: str, existing_slugs: List[str]) -> str:
    """Generate a unique slug by appending numbers if needed."""
    if base_slug not in existing_slugs:
        return base_slug
    
    counter = 1
    while f"{base_slug}-{counter}" in existing_slugs:
        counter += 1
    
    return f"{base_slug}-{counter}"

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


# === METADATA HELPERS ===

def create_field_metadata(
    title: str,
    description: str,
    example: Any = None,
    deprecated: bool = False
) -> Dict[str, Any]:
    """Create field metadata for auto-documentation."""
    metadata = {
        "title": title,
        "description": description
    }
    
    if example is not None:
        metadata["example"] = example
    
    if deprecated:
        metadata["deprecated"] = True
    
    return metadata

# ---- config.py ----
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
Application configuration schemas.
Provides schemas for system configuration and settings.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


def create_field_metadata(
    title: str,
    description: str,
    example: Optional[str] = None,
    **kwargs
) -> dict:
    """Create consistent field metadata for schema documentation."""
    metadata = {
        "title": title,
        "description": description,
        **kwargs
    }
    if example is not None:
        metadata["example"] = example
    return metadata


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AppConfig(BaseModel):
    """Application configuration schema."""
    
    app_name: str = Field(
        default="Goldleaves API",
        title="App Name", description="Application name"
    )
    
    debug: bool = Field(
        default=False,
        title="Debug Mode", description="Enable debug mode"
    )
    
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        title="Log Level", description="Application log level"
    )
    
    max_upload_size_mb: int = Field(
        default=100,
        title="Max Upload Size", description="Maximum file upload size in MB"
    )
    
    features: Dict[str, bool] = Field(
        default_factory=dict,
        title="Feature Flags", description="Feature toggle configuration"
    )
