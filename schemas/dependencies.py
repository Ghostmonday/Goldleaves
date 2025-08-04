"""
Shared schema dependencies and utilities.

This module re-exports common field validators and utilities from core_contracts
to maintain backwards compatibility with existing schema imports.
"""

from enum import Enum
from typing import Optional
from pydantic import Field

# Re-export functions from core_contracts for backwards compatibility
from .core_contracts import (
    non_empty_string,
    uuid_field,
    timestamp_field,
    validate_non_empty_string,
    email_field,
    LogLevel,
    PermissionLevel,
    create_field_metadata
)


class Status(str, Enum):
    """Generic status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    DELETED = "deleted"


def validation_field(
    validation_type: str,
    min_length: int = 1,
    max_length: int = 255,
    description: str = "Validation field"
) -> Field:
    """Create a validation field with consistent parameters."""
    return Field(
        min_length=min_length,
        max_length=max_length,
        description=description,
        title=validation_type.title()
    )


def enum_field(enum_class, description: str = "Enumeration field") -> Field:
    """Create an enum field with validation."""
    return Field(
        description=description,
        example=list(enum_class)[0].value if enum_class else None
    )
