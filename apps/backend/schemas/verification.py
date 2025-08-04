"""
Pydantic schemas for email verification endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

# Request Schemas
class SendVerificationRequest(BaseModel):
    """Request schema for sending verification email."""
    email: EmailStr = Field(..., description="User's email address")

class ConfirmVerificationRequest(BaseModel):
    """Request schema for confirming email verification."""
    token: str = Field(..., min_length=1, description="Verification token from email")

class ResendVerificationRequest(BaseModel):
    """Request schema for resending verification email."""
    email: EmailStr = Field(..., description="User's email address")

# Response Schemas
class VerificationResponse(BaseModel):
    """Standard response for verification operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message")
    expires_at: Optional[datetime] = Field(None, description="When the verification token expires")
    token: Optional[str] = Field(None, description="Verification token (development only)")

class ConfirmVerificationResponse(BaseModel):
    """Response schema for email confirmation."""
    success: bool = Field(..., description="Whether the verification was successful")
    message: str = Field(..., description="Human-readable message")
    user_id: Optional[int] = Field(None, description="ID of the verified user")

# Error Response Schema
class VerificationErrorResponse(BaseModel):
    """Error response for verification operations."""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
