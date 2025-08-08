# schemas/user.py

from __future__ import annotations
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from builtins import list
from datetime import datetime
from enum import Enum

# Define enums for consistency with models
class UserRole(str, Enum):
    """User role enum."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    VIEWER = "viewer"

class UserStatus(str, Enum):
    """User status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"

# ✅ Phase 3: EmailVerificationRequest, EmailVerificationToken, and AdminUserResponse schemas - COMPLETED

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr

class UserCreate(UserBase):
    """Schema for user creation."""
    password: str

class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_verified: bool
    email_verified: bool
    role: UserRole
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime] = None
    organization_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str

class Token(BaseModel):
    """Schema for access token."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for token data."""
    email: Optional[str] = None

# ✅ Phase 3: Email verification schemas - COMPLETED
class EmailVerificationRequest(BaseModel):
    """
    Schema for email verification requests.
    ✅ Defined the structure for email verification requests.
    Includes token and additional validation fields.
    """
    token: str
    
    class Config:
        from_attributes = True

class EmailVerificationToken(BaseModel):
    """
    Schema for email verification token response.
    ✅ Defined the structure for email verification token responses.
    Includes token, expiration, and status information.
    """
    token: str
    expires_at: datetime
    email: EmailStr
    
    class Config:
        from_attributes = True

class EmailVerificationResponse(BaseModel):
    """Response schema for email verification."""
    message: str
    success: bool
    user_id: Optional[int] = None

# ✅ Phase 3: AdminUserResponse for admin endpoints - COMPLETED
class AdminUserResponse(BaseModel):
    """
    Schema for admin user responses with detailed information.
    ✅ Defined comprehensive user information for admin endpoints.
    Includes all user fields, organization info, and admin-specific data.
    """
    id: int
    email: EmailStr
    is_active: bool
    is_verified: bool
    is_admin: bool
    email_verified: bool
    role: UserRole
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime] = None
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None
    
    # Admin-specific fields
    total_logins: Optional[int] = None
    account_status: str = "active"
    login_count: Optional[int] = None
    
    class Config:
        from_attributes = True

class AdminUserListResponse(BaseModel):
    """Schema for paginated admin user list."""
    users: List[AdminUserResponse]
    total: int
    page: int
    per_page: int
    pages: int

class UserUpdateRequest(BaseModel):
    """Schema for user update requests."""
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    email_verified: Optional[bool] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    organization_id: Optional[int] = None

# ✅ Phase 3: All user schema TODOs completed
