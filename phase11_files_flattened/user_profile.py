# schemas/frontend/user_profile.py
"""
Frontend-optimized user profile response schemas.
Provides clean, UI-ready data structures for user profile information.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserPlanType(str, Enum):
    """User subscription plan types."""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UserPreferences(BaseModel):
    """User UI preferences."""
    model_config = ConfigDict(from_attributes=True)
    
    theme: str = Field(default="light", description="UI theme preference")
    language: str = Field(default="en", description="Preferred language")
    timezone: str = Field(default="UTC", description="User timezone")
    date_format: str = Field(default="MM/DD/YYYY", description="Preferred date format")
    notifications_enabled: bool = Field(default=True, description="Email notifications enabled")
    desktop_notifications: bool = Field(default=True, description="Desktop notifications enabled")
    compact_view: bool = Field(default=False, description="Use compact UI view")
    sidebar_collapsed: bool = Field(default=False, description="Sidebar collapsed state")


class OrganizationSummary(BaseModel):
    """Simplified organization info for frontend."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Organization ID")
    name: str = Field(description="Organization name")
    role: str = Field(description="User's role in organization")
    member_count: int = Field(description="Total organization members")
    plan: UserPlanType = Field(description="Organization plan type")


class UserStats(BaseModel):
    """User activity statistics."""
    model_config = ConfigDict(from_attributes=True)
    
    documents_created: int = Field(default=0, description="Total documents created")
    documents_edited: int = Field(default=0, description="Total documents edited")
    cases_handled: int = Field(default=0, description="Total cases handled")
    clients_managed: int = Field(default=0, description="Total clients managed")
    storage_used_mb: float = Field(default=0.0, description="Storage used in MB")
    storage_limit_mb: float = Field(default=100.0, description="Storage limit in MB")


class UserCapabilities(BaseModel):
    """User permissions and capabilities."""
    model_config = ConfigDict(from_attributes=True)
    
    can_create_documents: bool = Field(default=True)
    can_delete_documents: bool = Field(default=False)
    can_manage_users: bool = Field(default=False)
    can_access_billing: bool = Field(default=False)
    can_export_data: bool = Field(default=True)
    can_use_ai_features: bool = Field(default=True)
    can_create_templates: bool = Field(default=False)
    is_admin: bool = Field(default=False)
    is_verified: bool = Field(default=False)


class UserProfileResponse(BaseModel):
    """Complete user profile response for frontend."""
    model_config = ConfigDict(from_attributes=True)
    
    # Basic info
    id: str = Field(description="User ID")
    email: str = Field(description="User email address")
    full_name: Optional[str] = Field(default=None, description="User's full name")
    avatar_url: Optional[str] = Field(default=None, description="Profile picture URL")
    
    # Account info
    created_at: datetime = Field(description="Account creation date")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    email_verified: bool = Field(default=False, description="Email verification status")
    account_status: str = Field(default="active", description="Account status")
    
    # Organization
    organization: Optional[OrganizationSummary] = Field(default=None, description="User's organization")
    
    # Preferences
    preferences: UserPreferences = Field(default_factory=UserPreferences, description="UI preferences")
    
    # Stats
    stats: UserStats = Field(default_factory=UserStats, description="User statistics")
    
    # Permissions
    capabilities: UserCapabilities = Field(default_factory=UserCapabilities, description="User permissions")
    
    # Additional metadata
    onboarding_completed: bool = Field(default=False, description="Onboarding status")
    requires_password_change: bool = Field(default=False, description="Password change required")
    has_two_factor: bool = Field(default=False, description="2FA enabled")
    
    # Session info
    session_expires_at: Optional[datetime] = Field(default=None, description="Current session expiry")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "usr_1234567890",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "avatar_url": "https://api.example.com/avatars/usr_1234567890.jpg",
                "created_at": "2024-01-15T10:30:00Z",
                "last_login": "2024-03-20T14:22:00Z",
                "email_verified": True,
                "account_status": "active",
                "organization": {
                    "id": "org_0987654321",
                    "name": "Acme Legal Services",
                    "role": "member",
                    "member_count": 25,
                    "plan": "pro"
                },
                "preferences": {
                    "theme": "dark",
                    "language": "en",
                    "timezone": "America/New_York",
                    "date_format": "MM/DD/YYYY",
                    "notifications_enabled": True,
                    "desktop_notifications": True,
                    "compact_view": False,
                    "sidebar_collapsed": False
                },
                "stats": {
                    "documents_created": 142,
                    "documents_edited": 89,
                    "cases_handled": 23,
                    "clients_managed": 15,
                    "storage_used_mb": 245.7,
                    "storage_limit_mb": 1000.0
                },
                "capabilities": {
                    "can_create_documents": True,
                    "can_delete_documents": True,
                    "can_manage_users": False,
                    "can_access_billing": False,
                    "can_export_data": True,
                    "can_use_ai_features": True,
                    "can_create_templates": True,
                    "is_admin": False,
                    "is_verified": True
                },
                "onboarding_completed": True,
                "requires_password_change": False,
                "has_two_factor": True,
                "session_expires_at": "2024-03-20T18:22:00Z"
            }
        }


class ProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile."""
    model_config = ConfigDict(from_attributes=True)
    
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    preferences: Optional[UserPreferences] = None
    avatar_url: Optional[str] = Field(default=None, max_length=500)
