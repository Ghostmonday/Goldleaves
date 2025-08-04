# schemas/frontend/__init__.py
"""
Frontend-optimized response schemas for Phase 11.
Provides clean, UI-ready data structures for frontend applications.
"""

from .user_profile import (
    UserProfileResponse,
    UserPreferences,
    OrganizationSummary,
    UserStats,
    UserCapabilities,
    ProfileUpdateRequest
)

from .documents import (
    DocumentListResponse,
    DocumentListItem,
    DocumentDetailResponse,
    DocumentFilter,
    DocumentSort,
    PaginationMeta
)

from .dashboard import (
    DashboardStatsResponse,
    StatCard,
    ActivityItem,
    ChartData,
    ChartDataPoint
)

from .forms import (
    FormMetadataResponse,
    FormField,
    FormSection,
    FormTemplate
)

__all__ = [
    # User Profile
    "UserProfileResponse",
    "UserPreferences", 
    "OrganizationSummary",
    "UserStats",
    "UserCapabilities",
    "ProfileUpdateRequest",
    
    # Documents
    "DocumentListResponse",
    "DocumentListItem", 
    "DocumentDetailResponse",
    "DocumentFilter",
    "DocumentSort",
    "PaginationMeta",
    
    # Dashboard
    "DashboardStatsResponse",
    "StatCard",
    "ActivityItem",
    "ChartData",
    "ChartDataPoint",
    
    # Forms
    "FormMetadataResponse",
    "FormField",
    "FormSection",
    "FormTemplate"
]
