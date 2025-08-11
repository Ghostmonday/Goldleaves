"""User schemas."""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

from schemas.base import PaginatedResponse


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


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")


class AuditSchema(TimestampSchema):
    """Schema with audit fields."""
    
    created_by: Optional[str] = Field(None, description="Created by user")
    updated_by: Optional[str] = Field(None, description="Updated by user")


class UserBase(BaseSchema):
    """Base user schema."""
    
    email: EmailStr = Field(..., description="Email address")
    username: Optional[str] = Field(None, description="Username")
    full_name: Optional[str] = Field(None, description="Full name")


class UserCreate(UserBase):
    """User creation schema."""
    
    password: str = Field(..., description="Password")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")


class UserUpdate(BaseSchema):
    """User update schema."""
    
    email: Optional[EmailStr] = Field(None, description="Email address")
    username: Optional[str] = Field(None, description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    status: Optional[str] = Field(None, description="User status")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")


class UserResponse(AuditSchema):
    """User response schema."""
    
    id: UUID = Field(..., description="User ID")
    email: EmailStr = Field(..., description="Email address")
    username: Optional[str] = Field(None, description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    status: str = Field(..., description="User status")
    email_verified: bool = Field(False, description="Email verification status")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")


class UserFilter(BaseSchema):
    """User filtering schema."""
    
    email: Optional[str] = Field(None, description="Filter by email")
    username: Optional[str] = Field(None, description="Filter by username")
    full_name: Optional[str] = Field(None, description="Filter by full name")
    status: Optional[str] = Field(None, description="Filter by status")
    organization_id: Optional[UUID] = Field(None, description="Filter by organization")
    email_verified: Optional[bool] = Field(None, description="Filter by email verification")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order")


class UserListResponse(PaginatedResponse):
    """User list response with pagination."""
    pass


class PasswordResetRequest(BaseSchema):
    """Password reset request schema."""
    
    email: EmailStr = Field(..., description="Email address")


class PasswordResetConfirm(BaseSchema):
    """Password reset confirmation schema."""
    
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., description="New password")
