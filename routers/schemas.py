# === AGENT CONTEXT: ROUTERS AGENT ===
# ✅ Phase 4: Complete schema definitions with validation

"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ===== USER SCHEMAS =====
class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class UserRegistrationSchema(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)
    organization_id: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe",
                "organization_id": "org_123"
            }
        }

class UserLoginSchema(BaseModel):
    """Schema for user login."""
    username_or_email: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)
    remember_me: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "username_or_email": "john@example.com",
                "password": "SecurePass123!",
                "remember_me": False
            }
        }

class UserProfileSchema(BaseModel):
    """Schema for user profile information."""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    status: UserStatus
    organization_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    email_verified: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "user_123",
                "username": "john_doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "role": "user",
                "status": "active",
                "organization_id": "org_123",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-01T00:00:00Z",
                "email_verified": True
            }
        }

class UserUpdateSchema(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v, values):
        """Validate new password if provided."""
        if v and not values.get('current_password'):
            raise ValueError('current_password is required when changing password')
        if v:
            # Apply same validation as registration
            if not any(c.isupper() for c in v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not any(c.islower() for c in v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not any(c.isdigit() for c in v):
                raise ValueError('Password must contain at least one digit')
            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
                raise ValueError('Password must contain at least one special character')
        return v

# ===== AUTHENTICATION SCHEMAS =====
class TokenSchema(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str = ""
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "refresh_token_here",
                "token_type": "bearer",
                "expires_in": 3600,
                "scope": "read write"
            }
        }

class TokenRefreshSchema(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "refresh_token_here"
            }
        }

class EmailVerificationSchema(BaseModel):
    """Schema for email verification."""
    token: str = Field(..., min_length=1, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "verification_token_here"
            }
        }

class ResendVerificationSchema(BaseModel):
    """Schema for resending verification email."""
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com"
            }
        }

class PasswordResetRequestSchema(BaseModel):
    """Schema for password reset request."""
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com"
            }
        }

class PasswordResetSchema(BaseModel):
    """Schema for password reset."""
    token: str = Field(..., min_length=1, max_length=500)
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

# ===== ADMIN SCHEMAS =====
class AdminUserListSchema(BaseModel):
    """Schema for admin user list response."""
    users: List[UserProfileSchema]
    total: int
    page: int
    per_page: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "users": [],
                "total": 100,
                "page": 1,
                "per_page": 10
            }
        }

class AdminUserUpdateSchema(BaseModel):
    """Schema for admin user updates."""
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    email_verified: Optional[bool] = None
    organization_id: Optional[str] = None

class AdminUserCreateSchema(BaseModel):
    """Schema for admin user creation."""
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    organization_id: Optional[str] = None
    email_verified: bool = True
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

# ===== RATE LIMITING SCHEMAS =====
class RateLimitStatusSchema(BaseModel):
    """Schema for rate limit status."""
    limit: int
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None
    allowed: bool = True
    algorithm_used: str = ""
    backend_used: str = ""
    
    class Config:
        json_schema_extra = {
            "example": {
                "limit": 100,
                "remaining": 75,
                "reset_time": 1640995200,
                "retry_after": None,
                "allowed": True,
                "algorithm_used": "sliding_window",
                "backend_used": "memory"
            }
        }

class RateLimitExceededSchema(BaseModel):
    """Schema for rate limit exceeded response."""
    detail: str = "Rate limit exceeded"
    retry_after: int
    limit: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Rate limit exceeded",
                "retry_after": 60,
                "limit": 100
            }
        }

# ===== ORGANIZATION SCHEMAS =====
class OrganizationSchema(BaseModel):
    """Schema for organization information."""
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    user_count: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "org_123",
                "name": "Acme Corporation",
                "description": "Leading tech company",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "user_count": 50
            }
        }

# ===== AUDIT SCHEMAS =====
class AuditLogSchema(BaseModel):
    """Schema for audit log entries."""
    id: str
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "audit_123",
                "user_id": "user_123",
                "action": "login",
                "resource_type": "user",
                "resource_id": "user_123",
                "details": {"method": "password"},
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

# ===== GENERIC RESPONSE SCHEMAS =====
class PaginationSchema(BaseModel):
    """Schema for pagination metadata."""
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "per_page": 10,
                "total": 100,
                "pages": 10
            }
        }

class MessageResponseSchema(BaseModel):
    """Schema for simple message responses."""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully"
            }
        }

class HealthCheckSchema(BaseModel):
    """Schema for health check response."""
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"
    environment: str = "development"
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
                "version": "1.0.0",
                "environment": "development"
            }
        }

# Export all schemas
__all__ = [
    # User schemas
    "UserRole", "UserStatus", "UserRegistrationSchema", "UserLoginSchema",
    "UserProfileSchema", "UserUpdateSchema",
    
    # Authentication schemas
    "TokenSchema", "TokenRefreshSchema", "EmailVerificationSchema",
    "ResendVerificationSchema", "PasswordResetRequestSchema", "PasswordResetSchema",
    
    # Admin schemas
    "AdminUserListSchema", "AdminUserUpdateSchema", "AdminUserCreateSchema",
    
    # Rate limiting schemas
    "RateLimitStatusSchema", "RateLimitExceededSchema",
    
    # Organization schemas
    "OrganizationSchema",
    
    # Audit schemas
    "AuditLogSchema",
    
    # Generic schemas
    "PaginationSchema", "MessageResponseSchema", "HealthCheckSchema"
]
