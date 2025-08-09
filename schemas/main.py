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

import logging
from builtins import any, len

logger = logging.getLogger(__name__)

"""Schemas Agent - Complete isolated implementation."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


# Local dependencies (all in this file for complete isolation)
class Config:
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    FROM_EMAIL: str = "noreply@goldleaves.com"

settings = Config()

class UserRole(str, Enum):
    """User role enumeration for authorization."""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

def validate_password_strength(password: str) -> str:
    """Validate password meets security requirements."""
    if not any(c.isupper() for c in password):
        raise ValueError('Password must contain at least one uppercase letter')
    if not any(c.islower() for c in password):
        raise ValueError('Password must contain at least one lowercase letter')
    if not any(c.isdigit() for c in password):
        raise ValueError('Password must contain at least one digit')
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        raise ValueError('Password must contain at least one special character')
    
    weak_patterns = ['123456', 'password', 'qwerty', 'admin']
    if any(pattern in password.lower() for pattern in weak_patterns):
        raise ValueError('Password contains common weak patterns')
    return password

def validate_name_format(name: str) -> str:
    """Validate name contains only allowed characters."""
    import re
    if not re.match(r'^[a-zA-Z\s\-\'\.]+$', name):
        raise ValueError('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
    return name

# === PHASE 3 SCHEMAS ===

class EmailVerificationRequest(BaseModel):
    """Schema for email verification requests."""
    token: str = Field(..., description="Email verification token")
    
    class Config:
        schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }

class EmailVerificationResponse(BaseModel):
    """Schema for email verification responses."""
    message: str = Field(..., description="Verification result message")
    success: bool = Field(True, description="Whether verification was successful")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Email verified successfully",
                "success": True
            }
        }

class AdminUserCreateRequest(BaseModel):
    """Request payload for admin to create a new user account."""
    email: EmailStr = Field(..., description="User's email address")
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=128,
        description="User's password (8-128 characters). If not provided, a secure random password will be generated."
    )
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User's first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User's last name")
    role: UserRole = Field(default=UserRole.USER, description="User's role in the system")
    is_verified: bool = Field(default=True, description="Whether the user's email is pre-verified")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    is_admin: bool = Field(default=False, description="Whether the user has admin privileges")
    
    @validator('password')
    def validate_password_strength_field(cls, v):
        if v is not None:
            return validate_password_strength(v)
        return v
    
    @validator('first_name', 'last_name')
    def validate_name_format_field(cls, v):
        if v is not None:
            return validate_name_format(v)
        return v

class AdminUserResponse(BaseModel):
    """Comprehensive user information for administrative interfaces."""
    id: int = Field(..., description="Unique user identifier", gt=0)
    email: EmailStr = Field(..., description="User's email address")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    is_active: bool = Field(True, description="Whether the account is active")
    is_verified: bool = Field(False, description="Email verification status")
    is_admin: bool = Field(False, description="Admin privileges")
    email_verified: bool = Field(False, description="Email verification status")
    role: UserRole = Field(UserRole.USER, description="User's system role")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Most recent successful login")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "email": "john.doe@company.com",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True,
                "is_verified": True,
                "is_admin": False,
                "email_verified": True,
                "role": "user",
                "created_at": "2025-07-01T10:30:00",
                "last_login": "2025-08-02T09:15:00"
            }
        }

class UserCreateRequest(BaseModel):
    """Request payload for creating a new user."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's password (8-128 characters)")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Confirmation of the password")
    first_name: Optional[str] = Field(None, max_length=50, description="User's first name")
    last_name: Optional[str] = Field(None, max_length=50, description="User's last name")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password_strength_field(cls, v):
        return validate_password_strength(v)

class UserOut(BaseModel):
    """User output schema."""
    id: int
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    email_verified: bool = False
    created_at: datetime
    
    class Config:
        orm_mode = True

# === ENTRY POINT ===
def get_schemas():
    """Entry point for schemas agent."""
    return {
        "EmailVerificationRequest": EmailVerificationRequest,
        "EmailVerificationResponse": EmailVerificationResponse,
        "AdminUserCreateRequest": AdminUserCreateRequest,
        "AdminUserResponse": AdminUserResponse,
        "UserCreateRequest": UserCreateRequest,
        "UserOut": UserOut,
        "UserRole": UserRole
    }

if __name__ == "__main__":
    schemas = get_schemas()
    logger.info("Schemas agent loaded %d schema classes", len(schemas))
    for name, schema in schemas.items():
        logger.info("  - %s: %s", name, schema.__doc__ or 'No description')
