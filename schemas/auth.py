"""Authentication schemas."""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime



class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Token(BaseSchema):
    """Token response schema."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class UserLogin(BaseSchema):
    """User login schema."""
    
    username_or_email: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class UserRegister(BaseSchema):
    """User registration schema."""
    
    email: EmailStr = Field(..., description="Email address")
    username: Optional[str] = Field(None, description="Username")
    password: str = Field(..., description="Password")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    full_name: Optional[str] = Field(None, description="Full name")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserCreate(BaseSchema):
    """User creation schema (admin only)."""
    
    email: EmailStr = Field(..., description="Email address")
    username: Optional[str] = Field(None, description="Username")
    password: str = Field(..., description="Password")
    full_name: Optional[str] = Field(None, description="Full name")
    organization_id: Optional[str] = Field(None, description="Organization ID")


class EmailVerification(BaseSchema):
    """Email verification schema."""
    
    token: str = Field(..., description="Verification token")


class PasswordReset(BaseSchema):
    """Password reset request schema."""
    
    email: EmailStr = Field(..., description="Email address")


class PasswordResetConfirm(BaseSchema):
    """Password reset confirmation schema."""
    
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
