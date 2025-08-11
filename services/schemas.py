# schemas.py

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: int = Field(..., description="Expiration timestamp for access token")
    refresh_expires_at: int = Field(..., description="Expiration timestamp for refresh token")

class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: Optional[str] = None
    exp: Optional[datetime] = None
    jti: Optional[str] = None
    refresh: Optional[bool] = False

class EmailVerificationRequest(BaseModel):
    """Schema for email verification request."""
    token: str = Field(..., description="Email verification token", min_length=1)
    
    @validator('token')
    def validate_token(cls, v):
        if not v or not v.strip():
            raise ValueError('Token cannot be empty')
        return v.strip()

class EmailVerificationToken(BaseModel):
    """Schema for email verification token response."""
    verification_token: str = Field(..., description="JWT token for email verification")
    user_id: str = Field(..., description="User ID associated with the token")
    email: str = Field(..., description="Email address to verify")
    expires_at: int = Field(..., description="Expiration timestamp for the token")
    token_type: str = Field(default="email_verification", description="Type of token")

class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"

class AdminUserResponse(BaseModel):
    """Schema for admin user response with filtered information."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    username: Optional[str] = Field(None, description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    role: UserRole = Field(..., description="User role")
    status: UserStatus = Field(..., description="User status")
    is_email_verified: bool = Field(default=False, description="Whether email is verified")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    login_count: int = Field(default=0, description="Total number of logins")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AdminUsersListResponse(BaseModel):
    """Schema for paginated admin users list response."""
    users: List[AdminUserResponse] = Field(..., description="List of users")
    total_count: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number", ge=1)
    page_size: int = Field(..., description="Number of users per page", ge=1, le=100)
    total_pages: int = Field(..., description="Total number of pages")
    
class EmailVerificationResponse(BaseModel):
    """Schema for successful email verification response."""
    message: str = Field(default="Email verified successfully", description="Success message")
    user_id: str = Field(..., description="ID of the verified user")
    email: str = Field(..., description="Verified email address")
    verified_at: datetime = Field(..., description="Verification timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
