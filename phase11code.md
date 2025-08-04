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


















    # schemas/frontend/documents.py
"""
Frontend-optimized document response schemas.
Provides clean, UI-ready data structures for document listings and details.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Document type enumeration."""
    FORM = "form"
    TEMPLATE = "template"
    CONTRACT = "contract"
    LETTER = "letter"
    REPORT = "report"
    MEMO = "memo"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Document status enumeration."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SIGNED = "signed"
    ARCHIVED = "archived"


class DocumentPermissions(BaseModel):
    """Document-specific permissions for current user."""
    model_config = ConfigDict(from_attributes=True)
    
    can_view: bool = Field(default=True)
    can_edit: bool = Field(default=False)
    can_delete: bool = Field(default=False)
    can_share: bool = Field(default=False)
    can_download: bool = Field(default=True)
    can_comment: bool = Field(default=True)
    can_sign: bool = Field(default=False)


class DocumentAuthor(BaseModel):
    """Simplified author information."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Author user ID")
    name: str = Field(description="Author display name")
    email: str = Field(description="Author email")
    avatar_url: Optional[str] = Field(default=None, description="Author avatar URL")


class DocumentTag(BaseModel):
    """Document tag/label."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Tag ID")
    name: str = Field(description="Tag name")
    color: str = Field(default="#6B7280", description="Tag color hex code")


class DocumentVersion(BaseModel):
    """Document version information."""
    model_config = ConfigDict(from_attributes=True)
    
    version_number: int = Field(description="Version number")
    created_at: datetime = Field(description="Version creation timestamp")
    created_by: DocumentAuthor = Field(description="Version creator")
    change_summary: Optional[str] = Field(default=None, description="Summary of changes")
    size_bytes: int = Field(description="Version size in bytes")


class DocumentListItem(BaseModel):
    """Simplified document item for list views."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Document ID")
    title: str = Field(description="Document title")
    type: DocumentType = Field(description="Document type")
    status: DocumentStatus = Field(description="Document status")
    
    # Key metadata
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    created_by: DocumentAuthor = Field(description="Document creator")
    
    # Quick stats
    size_bytes: int = Field(description="Document size in bytes")
    page_count: Optional[int] = Field(default=None, description="Number of pages")
    version_count: int = Field(default=1, description="Number of versions")
    
    # UI helpers
    thumbnail_url: Optional[str] = Field(default=None, description="Document thumbnail URL")
    preview_text: Optional[str] = Field(default=None, description="Preview text snippet")
    tags: List[DocumentTag] = Field(default_factory=list, description="Document tags")
    
    # Collaboration info
    shared_with_count: int = Field(default=0, description="Number of users with access")
    comment_count: int = Field(default=0, description="Number of comments")
    is_favorite: bool = Field(default=False, description="Favorited by current user")
    
    # Permissions
    permissions: DocumentPermissions = Field(description="Current user permissions")
    
    # Related entities
    case_id: Optional[str] = Field(default=None, description="Associated case ID")
    client_id: Optional[str] = Field(default=None, description="Associated client ID")


class DocumentFilter(BaseModel):
    """Document filter options."""
    model_config = ConfigDict(from_attributes=True)
    
    search: Optional[str] = Field(default=None, description="Search query")
    type: Optional[List[DocumentType]] = Field(default=None, description="Filter by types")
    status: Optional[List[DocumentStatus]] = Field(default=None, description="Filter by status")
    created_by: Optional[List[str]] = Field(default=None, description="Filter by creator IDs")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tag IDs")
    case_id: Optional[str] = Field(default=None, description="Filter by case")
    client_id: Optional[str] = Field(default=None, description="Filter by client")
    date_from: Optional[datetime] = Field(default=None, description="Filter by date range start")
    date_to: Optional[datetime] = Field(default=None, description="Filter by date range end")
    is_favorite: Optional[bool] = Field(default=None, description="Filter favorites only")
    shared_with_me: Optional[bool] = Field(default=None, description="Filter shared documents")


class DocumentSort(BaseModel):
    """Document sort options."""
    model_config = ConfigDict(from_attributes=True)
    
    field: Literal["title", "created_at", "updated_at", "size_bytes", "type", "status"] = Field(
        default="updated_at",
        description="Sort field"
    )
    order: Literal["asc", "desc"] = Field(default="desc", description="Sort order")


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    model_config = ConfigDict(from_attributes=True)
    
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total_items: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Has next page")
    has_previous: bool = Field(description="Has previous page")


class DocumentListResponse(BaseModel):
    """Document list response with pagination and metadata."""
    model_config = ConfigDict(from_attributes=True)
    
    documents: List[DocumentListItem] = Field(description="List of documents")
    pagination: PaginationMeta = Field(description="Pagination information")
    
    # Applied filters (for UI state)
    applied_filters: DocumentFilter = Field(description="Currently applied filters")
    applied_sort: DocumentSort = Field(description="Currently applied sort")
    
    # Quick stats
    total_size_bytes: int = Field(default=0, description="Total size of all documents")
    type_breakdown: Dict[DocumentType, int] = Field(
        default_factory=dict,
        description="Document count by type"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "id": "doc_abc123",
                        "title": "Employment Agreement - John Smith",
                        "type": "contract",
                        "status": "in_review",
                        "created_at": "2024-03-15T09:30:00Z",
                        "updated_at": "2024-03-19T16:45:00Z",
                        "created_by": {
                            "id": "usr_123",
                            "name": "Jane Doe",
                            "email": "jane.doe@example.com",
                            "avatar_url": "https://api.example.com/avatars/usr_123.jpg"
                        },
                        "size_bytes": 245760,
                        "page_count": 8,
                        "version_count": 3,
                        "thumbnail_url": "https://api.example.com/thumbnails/doc_abc123.jpg",
                        "preview_text": "This Employment Agreement is entered into as of...",
                        "tags": [
                            {"id": "tag_1", "name": "Employment", "color": "#10B981"},
                            {"id": "tag_2", "name": "Urgent", "color": "#EF4444"}
                        ],
                        "shared_with_count": 3,
                        "comment_count": 5,
                        "is_favorite": True,
                        "permissions": {
                            "can_view": True,
                            "can_edit": True,
                            "can_delete": False,
                            "can_share": True,
                            "can_download": True,
                            "can_comment": True,
                            "can_sign": False
                        },
                        "case_id": "case_xyz789",
                        "client_id": "client_def456"
                    }
                ],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total_items": 142,
                    "total_pages": 8,
                    "has_next": True,
                    "has_previous": False
                },
                "applied_filters": {
                    "search": None,
                    "type": ["contract"],
                    "status": ["draft", "in_review"],
                    "is_favorite": None
                },
                "applied_sort": {
                    "field": "updated_at",
                    "order": "desc"
                },
                "total_size_bytes": 52428800,
                "type_breakdown": {
                    "contract": 45,
                    "form": 38,
                    "letter": 29,
                    "template": 20,
                    "report": 10
                }
            }
        }


class DocumentDetailResponse(DocumentListItem):
    """Detailed document response with full content."""
    model_config = ConfigDict(from_attributes=True)
    
    # Additional detail fields
    content_url: Optional[str] = Field(default=None, description="URL to fetch document content")
    download_url: Optional[str] = Field(default=None, description="Direct download URL")
    
    # Full version history
    versions: List[DocumentVersion] = Field(default_factory=list, description="Version history")
    
    # Sharing details
    shared_with: List[DocumentAuthor] = Field(default_factory=list, description="Users with access")
    public_link: Optional[str] = Field(default=None, description="Public sharing link")
    
    # Metadata
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    
    # Related documents
    related_documents: List[DocumentListItem] = Field(
        default_factory=list,
        description="Related documents"
    )



















    UNFINISHED

    # schemas/frontend/dashboard.py
"""
Frontend-optimized dashboard and stats response schemas.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from enum import Enum


class TrendDirection(str, Enum):
    """Trend direction for statistics."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class StatCard(BaseModel):
    """Individual statistic card for dashboard."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Stat card identifier")
    title: str = Field(description="Card title")
    value: float = Field(description="Current value")
    unit: str = Field(default="", description="Value unit (e.g., 'documents', '%')")
    change_percent: float = Field(default=0.0, description="Percentage change")
    trend: TrendDirection = Field(default=TrendDirection.STABLE, description="Trend direction")
    icon: str = Field(default="chart", description="Icon name for UI")
    color: str = Field(default="#6B7280", description="Card color")


class ActivityItem(BaseModel):
    """Recent activity item."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Activity ID")
    type: str = Field(description="Activity type")
    title: str = Field(description="Activity title")
    description: str = Field(description="Activity description")
    timestamp: datetime = Field(description="When activity occurred")
    user: Dict[str, str] = Field(description="User who performed activity")
    entity_type: str = Field(description="Related entity type")
    entity_id: str = Field(description="Related entity ID")
    entity_title: str = Field(description="Related entity title")


class ChartDataPoint(BaseModel):
    """Single data point for charts."""
    model_config = ConfigDict(from_attributes=True)
    
    label: str = Field(description="Data point label")
    value: float = Field(description="Data point value")
    date: Optional[date] = Field(default=None, description="Date for time series")


class ChartData(BaseModel):
    """Chart data structure."""
    model_config = ConfigDict(from_attributes=True)
    
    title: str = Field(description="Chart title")
    type: str = Field(description="Chart type (line, bar, pie)")
    data: List[ChartDataPoint] = Field(description="Chart data points")
    unit: str = Field(default="", description="Y-axis unit")


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics and overview response."""
    model_config = ConfigDict(from_attributes=True)
    
    # Summary stats
    stats_cards: List[StatCard] = Field(description="Key statistics cards")
    
    # Activity feed
    recent_activity: List[ActivityItem] = Field(description="Recent activity items")
    
    # Charts
    charts: List[ChartData] = Field(description="Dashboard charts")
    
    # Quick actions
    quick_actions: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Available quick actions"
    )
    
    # Announcements
    announcements: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="System announcements"
    )
    
    # Last updated
    last_updated: datetime = Field(description="Dashboard data last updated")


# schemas/frontend/forms.py
"""
Frontend-optimized form metadata response schemas.
"""


class FormFieldType(str, Enum):
    """Form field types."""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXTAREA = "textarea"
    FILE = "file"
    SIGNATURE = "signature"


class FormField(BaseModel):
    """Form field definition."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Field ID")
    name: str = Field(description="Field name")
    label: str = Field(description="Field label")
    type: FormFieldType = Field(description="Field type")
    required: bool = Field(default=False, description="Is field required")
    placeholder: Optional[str] = Field(default=None, description="Field placeholder")
    help_text: Optional[str] = Field(default=None, description="Field help text")
    default_value: Optional[Any] = Field(default=None, description="Default value")
    options: Optional[List[Dict[str, str]]] = Field(default=None, description="Options for select/radio")
    validation: Optional[Dict[str, Any]] = Field(default=None, description="Validation rules")
    conditional: Optional[Dict[str, Any]] = Field(default=None, description="Conditional display rules")


class FormSection(BaseModel):
    """Form section containing fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Section ID")
    title: str = Field(description="Section title")
    description: Optional[str] = Field(default=None, description="Section description")
    fields: List[FormField] = Field(description="Fields in this section")
    order: int = Field(description="Section display order")


class FormTemplate(BaseModel):
    """Form template metadata."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Template ID")
    name: str = Field(description="Template name")
    description: str = Field(description="Template description")
    category: str = Field(description="Template category")
    version: str = Field(default="1.0", description="Template version")
    is_active: bool = Field(default=True, description="Is template active")
    usage_count: int = Field(default=0, description="Times template used")
    last_updated: datetime = Field(description="Last update timestamp")
    created_by: Dict[str, str] = Field(description="Template creator")
    tags: List[str] = Field(default_factory=list, description="Template tags")


class FormMetadataResponse(BaseModel):
    """Form metadata and structure response."""
    model_config = ConfigDict(from_attributes=True)
    
    form_id: str = Field(description="Form ID")
    title: str = Field(description="Form title")
    description: str = Field(description="Form description")
    
    # Form structure
    sections: List[FormSection] = Field(description="Form sections")
    
    # Metadata
    template: Optional[FormTemplate] = Field(default=None, description="Base template info")
    version: int = Field(default=1, description="Form version")
    is_published: bool = Field(default=False, description="Is form published")
    
    # Settings
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Form settings (submission limits, etc.)"
    )
    
    # Permissions
    can_submit: bool = Field(default=True, description="Can current user submit")
    can_edit: bool = Field(default=False, description="Can current user edit")
    
    # Stats
    submission_count: int = Field(default=0, description="Number of submissions")
    completion_rate: float = Field(default=0.0, description="Average completion rate")
    
    # Timestamps
    created_at: datetime = Field(description="Form creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    published_at: Optional[datetime] = Field(default=None, description="Publication timestamp")


# schemas/frontend/notifications.py
"""
Frontend-optimized notification response schemas.
"""


class NotificationType(str, Enum):
    """Notification types."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    MENTION = "mention"
    ASSIGNMENT = "assignment"
    COMMENT = "comment"
    SYSTEM = "system"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationAction(BaseModel):
    """Action button for notification."""
    model_config = ConfigDict(from_attributes=True)
    
    label: str = Field(description="Action button label")
    action: str = Field(description="Action identifier")
    url: Optional[str] = Field(default=None, description="Action URL")
    style: str = Field(default="default", description="Button style")


class NotificationItem(BaseModel):
    """Individual notification item."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Notification ID")
    type: NotificationType = Field(description="Notification type")
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM)
    
    # Content
    title: str = Field(description="Notification title")
    message: str = Field(description="Notification message")
    icon: str = Field(default="bell", description="Icon name")
    
    # Metadata
    created_at: datetime = Field(description="Creation timestamp")
    read_at: Optional[datetime] = Field(default=None, description="Read timestamp")
    is_read: bool = Field(default=False, description="Read status")
    
    # Source
    source: Dict[str, str] = Field(description="Notification source")
    related_entity: Optional[Dict[str, str]] = Field(default=None, description="Related entity")
    
    # Actions
    actions: List[NotificationAction] = Field(default_factory=list, description="Available actions")
    
    # Grouping
    group_id: Optional[str] = Field(default=None, description="Notification group ID")
    group_count: int = Field(default=1, description="Number in group")


class NotificationGroup(BaseModel):
    """Grouped notifications."""
    model_config = ConfigDict(from_attributes=True)
    
    group_id: str = Field(description="Group ID")
    group_type: str = Field(description="Group type")
    title: str = Field(description="Group title")
    count: int = Field(description="Notifications in group")
    latest_timestamp: datetime = Field(description="Latest notification time")
    notifications: List[NotificationItem] = Field(description="Grouped notifications")


class NotificationPreferences(BaseModel):
    """User notification preferences."""
    model_config = ConfigDict(from_attributes=True)
    
    email_enabled: bool = Field(default=True, description="Email notifications enabled")
    push_enabled: bool = Field(default=True, description="Push notifications enabled")
    desktop_enabled: bool = Field(default=True, description="Desktop notifications enabled")
    
    # Per-type preferences
    type_preferences: Dict[NotificationType, bool] = Field(
        default_factory=dict,
        description="Enabled status per notification type"
    )
    
    # Quiet hours
    quiet_hours_enabled: bool = Field(default=False, description="Quiet hours enabled")
    quiet_hours_start: Optional[str] = Field(default=None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: Optional[str] = Field(default=None, description="Quiet hours end (HH:MM)")


class NotificationFeedResponse(BaseModel):
    """Notification feed response with pagination."""
    model_config = ConfigDict(from_attributes=True)
    
    # Notifications
    notifications: List[NotificationItem] = Field(description="List of notifications")
    groups: List[NotificationGroup] = Field(default_factory=list, description="Grouped notifications")
    
    # Counts
    unread_count: int = Field(default=0, description="Total unread notifications")
    total_count: int = Field(default=0, description="Total notifications")
    
    # Pagination
    has_more: bool = Field(default=False, description="More notifications available")
    next_cursor: Optional[str] = Field(default=None, description="Cursor for next page






    VERSION 2?
    # routers/api/v2/frontend_sync.py
"""
Frontend-facing API v2 router with optimized endpoints for UI consumption.
Implements aggregated, simplified responses with proper caching and pagination.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

# Import schemas
from schemas.frontend.user_profile import UserProfileResponse, ProfileUpdateRequest
from schemas.frontend.documents import (
    DocumentListResponse, DocumentFilter, DocumentSort, 
    PaginationMeta, DocumentListItem, DocumentType, DocumentStatus
)
from schemas.frontend.dashboard import DashboardStatsResponse
from schemas.frontend.forms import FormMetadataResponse
from schemas.frontend.notifications import NotificationFeedResponse

# Import dependencies
from core.dependencies import get_current_active_user
from models.user import User
from services.frontend_session.session_store import FrontendSessionStore
from services.frontend_session.activity_tracker import ActivityTracker
from services.realtime.broadcaster import RealtimeBroadcaster

# Initialize router
router = APIRouter(
    prefix="/api/v2",
    tags=["frontend"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        500: {"description": "Internal server error"}
    }
)

# Initialize services
session_store = FrontendSessionStore()
activity_tracker = ActivityTracker()
broadcaster = RealtimeBroadcaster()


def create_error_response(error: str, status_code: int = 400) -> JSONResponse:
    """Create standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": error,
            "data": None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


def create_success_response(data: Any, cache_seconds: Optional[int] = None) -> JSONResponse:
    """Create standardized success response with optional caching."""
    headers = {}
    if cache_seconds:
        headers["Cache-Control"] = f"public, max-age={cache_seconds}"
    
    return JSONResponse(
        content={
            "success": True,
            "error": None,
            "data": json.loads(data.model_dump_json()) if hasattr(data, 'model_dump_json') else data,
            "timestamp": datetime.utcnow().isoformat()
        },
        headers=headers
    )


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    include_stats: bool = Query(True, description="Include usage statistics"),
    include_preferences: bool = Query(True, description="Include UI preferences")
) -> JSONResponse:
    """
    Get current user's profile with UI-optimized data.
    
    Returns comprehensive user profile including preferences, permissions,
    organization info, and usage statistics.
    """
    try:
        # Build user profile response
        profile_data = {
            "id": f"usr_{current_user.id}",
            "email": current_user.email,
            "full_name": getattr(current_user, 'full_name', None),
            "avatar_url": getattr(current_user, 'avatar_url', None),
            "created_at": current_user.created_at,
            "last_login": current_user.last_login,
            "email_verified": current_user.email_verified,
            "account_status": current_user.status.value,
            "onboarding_completed": getattr(current_user, 'onboarding_completed', True),
            "requires_password_change": False,
            "has_two_factor": False,
            "session_expires_at": datetime.utcnow() + timedelta(hours=8)
        }
        
        # Add organization info if available
        if current_user.organization:
            profile_data["organization"] = {
                "id": f"org_{current_user.organization.id}",
                "name": current_user.organization.name,
                "role": "member",  # Would come from role assignment
                "member_count": 10,  # Would be calculated
                "plan": current_user.organization.plan.value
            }
        
        # Get preferences from session store
        if include_preferences:
            preferences = await session_store.get_preferences(current_user.id)
            profile_data["preferences"] = preferences or {}
        
        # Calculate stats if requested
        if include_stats:
            stats = await activity_tracker.get_user_stats(current_user.id)
            profile_data["stats"] = stats
        
        # Build capabilities based on user role and permissions
        profile_data["capabilities"] = {
            "can_create_documents": True,
            "can_delete_documents": current_user.role.value in ["admin", "moderator"],
            "can_manage_users": current_user.is_admin,
            "can_access_billing": current_user.is_admin or (current_user.organization and current_user.organization.plan.value != "free"),
            "can_export_data": True,
            "can_use_ai_features": current_user.organization and current_user.organization.plan.value in ["pro", "enterprise"],
            "can_create_templates": current_user.role.value in ["admin", "moderator"],
            "is_admin": current_user.is_admin,
            "is_verified": current_user.is_verified
        }
        
        response = UserProfileResponse(**profile_data)
        
        # Track activity
        await activity_tracker.track_activity(
            user_id=current_user.id,
            activity_type="profile_viewed",
            metadata={"timestamp": datetime.utcnow()}
        )
        
        # Cache for 5 minutes
        return create_success_response(response, cache_seconds=300)
        
    except Exception as e:
        return create_error_response(f"Failed to load profile: {str(e)}", 500)


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: ProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """Update user profile information."""
    try:
        # Update preferences if provided
        if profile_update.preferences:
            await session_store.update_preferences(
                current_user.id,
                profile_update.preferences.model_dump()
            )
        
        # Here we would update user fields in database
        # For now, just return updated profile
        
        # Broadcast profile update
        await broadcaster.broadcast_user_update(
            user_id=current_user.id,
            update_type="profile",
            data=profile_update.model_dump(exclude_none=True)
        )
        
        # Return updated profile
        return await get_user_profile(current_user)
        
    except Exception as e:
        return create_error_response(f"Failed to update profile: {str(e)}", 500)


@router.get("/documents", response_model=DocumentListResponse)
async def get_documents(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    
    # Filters
    search: Optional[str] = Query(None, description="Search query"),
    type: Optional[List[DocumentType]] = Query(None, description="Filter by document types"),
    status: Optional[List[DocumentStatus]] = Query(None, description="Filter by status"),
    created_by: Optional[List[str]] = Query(None, description="Filter by creator IDs"),
    tags: Optional[List[str]] = Query(None, description="Filter by tag IDs"),
    case_id: Optional[str] = Query(None, description="Filter by case"),
    client_id: Optional[str] = Query(None, description="Filter by client"),
    is_favorite: Optional[bool] = Query(None, description="Filter favorites only"),
    shared_with_me: Optional[bool] = Query(None, description="Filter shared documents"),
    
    # Sorting
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    
    # Sparse fieldsets
    fields: Optional[List[str]] = Query(None, description="Fields to include"),
    
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    Get paginated document list with filters and sorting.
    
    Supports advanced filtering, sorting, pagination, and sparse fieldsets
    for optimal performance.
    """
    try:
        # Build filter object
        filters = DocumentFilter(
            search=search,
            type=type,
            status=status,
            created_by=created_by,
            tags=tags,
            case_id=case_id,
            client_id=client_id,
            is_favorite=is_favorite,
            shared_with_me=shared_with_me
        )
        
        # Build sort object
        sort = DocumentSort(field=sort_by, order=sort_order)
        
        # Mock document data - in production, this would query the database
        mock_documents = []
        for i in range(5):
            doc = DocumentListItem(
                id=f"doc_{i+1}",
                title=f"Sample Document {i+1}",
                type=DocumentType.CONTRACT if i % 2 == 0 else DocumentType.FORM,
                status=DocumentStatus.DRAFT if i < 2 else DocumentStatus.IN_REVIEW,
                created_at=datetime.utcnow() - timedelta(days=i),
                updated_at=datetime.utcnow() - timedelta(hours=i*2),
                created_by={
                    "id": f"usr_{current_user.id}",
                    "name": "Current User",
                    "email": current_user.email,
                    "avatar_url": None
                },
                size_bytes=1024 * (100 + i * 50),
                page_count=5 + i,
                version_count=1 + (i // 2),
                tags=[],
                shared_with_count=i,
                comment_count=i * 2,
                is_favorite=i == 0,
                permissions={
                    "can_view": True,
                    "can_edit": i < 3,
                    "can_delete": i < 2,
                    "can_share": True,
                    "can_download": True,
                    "can_comment": True,
                    "can_sign": False
                }
            )
            mock_documents.append(doc)
        
        # Build pagination meta
        total_items = 142  # Mock total
        pagination = PaginationMeta(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=(total_items + per_page - 1) // per_page,
            has_next=page * per_page < total_items,
            has_previous=page > 1
        )
        
        # Build response
        response = DocumentListResponse(
            documents=mock_documents,
            pagination=pagination,
            applied_filters=filters,
            applied_sort=sort,
            total_size_bytes=52428800,
            type_breakdown={
                DocumentType.CONTRACT: 45,
                DocumentType.FORM: 38,
                DocumentType.LETTER: 29,
                DocumentType.TEMPLATE: 20,
                DocumentType.REPORT: 10
            }
        )
        
        # Track activity
        await activity_tracker.track_activity(
            user_id=current_user.id,
            activity_type="documents_viewed",
            metadata={
                "page": page,
                "filters": filters.model_dump(exclude_none=True)
            }
        )
        
        # Cache for 60 seconds
        return create_success_response(response, cache_seconds=60)
        
    except Exception as e:
        return create_error_response(f"Failed to load documents: {str(e)}", 500)


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    date_range: str = Query("30d", description="Date range for stats (7d, 30d, 90d)")
) -> JSONResponse:
    """Get dashboard statistics and overview data."""
    try:
        # Mock dashboard data
        stats_cards = [
            {
                "id": "total_documents",
                "title": "Total Documents",
                "value": 142,
                "unit": "documents",
                "change_percent": 12.5,
                "trend": "up",
                "icon": "document",
                "color": "#3B82F6"
            },
            {
                "id": "active_cases",
                "title": "Active Cases",
                "value": 23,
                "unit": "cases",
                "change_percent": -5.2,
                "trend": "down",
                "icon": "briefcase",
                "color": "#10B981"
            },
            {
                "id": "storage_used",
                "title": "Storage Used",
                "value": 24.5,
                "unit": "%",
                "change_percent": 8.3,
                "trend": "up",
                "icon": "database",
                "color": "#F59E0B"
            }
        ]
        
        recent_activity = [
            {
                "id": "act_1",
                "type": "document_created",
                "title": "New document created",
                "description": "Employment Agreement - John Smith was created",
                "timestamp": datetime.utcnow() - timedelta(minutes=30),
                "user": {"id": "usr_123", "name": "Jane Doe"},
                "entity_type": "document",
                "entity_id": "doc_abc123",
                "entity_title": "Employment Agreement - John Smith"
            }
        ]
        
        charts = [
            {
                "title": "Documents Created",
                "type": "line",
                "data": [
                    {"label": "Mon", "value": 5, "date": None},
                    {"label": "Tue", "value": 8, "date": None},
                    {"label": "Wed", "value": 12, "date": None},
                    {"label": "Thu", "value": 10, "date": None},
                    {"label": "Fri", "value": 15, "date": None}
                ],
                "unit": "documents"
            }
        ]
        
        response = DashboardStatsResponse(
            stats_cards=stats_cards,
            recent_activity=recent_activity,
            charts=charts,
            quick_actions=[
                {"id": "new_doc", "label": "New Document", "icon": "plus"},
                {"id": "new_case", "label": "New Case", "icon": "briefcase"}
            ],
            announcements=[],
            last_updated=datetime.utcnow()
        )
        
        # Cache for 5 minutes
        return create_success_response(response, cache_seconds=300)
        
    except Exception as e:
        return create_error_response(f"Failed to load dashboard: {str(e)}", 500)


@router.get("/forms/{form_id}", response_model=FormMetadataResponse)
async def get_form_metadata(
    form_id: str,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """Get form metadata and structure."""
    try:
        # Mock form data
        response = FormMetadataResponse(
            form_id=form_id,
            title="Employment Agreement Form",
            description="Standard employment agreement template",
            sections=[
                {
                    "id": "sec_1",
                    "title": "Employee Information",
                    "description": "Basic employee details",
                    "fields": [
                        {
                            "id": "field_1",
                            "name": "full_name",
                            "label": "Full Name",
                            "type": "text",
                            "required": True,
                            "placeholder": "Enter full name"
                        }
                    ],
                    "order": 1
                }
            ],
            version=1,
            is_published=True,
            settings={},
            can_submit=True,
            can_edit=current_user.is_admin,
            submission_count=0,
            completion_rate=0.0,
            created_at=datetime.utcnow() - timedelta(days=7),
            updated_at=datetime.utcnow()
        )
        
        # Cache for 10 minutes
        return create_success_response(response, cache_seconds=600)
        
    except Exception as e:
        return create_error_response(f"Failed to load form: {str(e)}", 500)


@router.get("/notifications", response_model=NotificationFeedResponse)
async def get_notifications(
    unread_only: bool = Query(False, description="Show only unread notifications"),
    limit: int = Query(20, ge=1, le=100, description="Number of notifications to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """Get user notifications with pagination."""
    try:
        # Mock notification data
        notifications = []
        for i in range(5):
            notif = {
                "id": f"notif_{i+1}",
                "type": "info" if i % 2 == 0 else "mention",
                "priority": "medium",
                "title": f"Notification {i+1}",
                "message": f"This is notification message {i+1}",
                "icon": "bell",
                "created_at": datetime.utcnow() - timedelta(hours=i),
                "read_at": None if i < 2 else datetime.utcnow() - timedelta(hours=i-2),
                "is_read": i >= 2,
                "source": {"type": "system", "id": "system"},
                "actions": []
            }
            notifications.append(notif)
        
        response = NotificationFeedResponse(
            notifications=notifications,
            groups=[],
            unread_count=2,
            total_count=5,
            has_more=False,
            next_cursor=None
        )
        
        # No caching for notifications
        return create_success_response(response)
        
    except Exception as e:
        return create_error_response(f"Failed to load notifications: {str(e)}", 500)


# Health check endpoint
@router.get("/health")
async def health_check():
    """API health check endpoint."""
    return create_success_response({
        "status": "healthy",
        "version": "2.0",
        "timestamp": datetime.utcnow().isoformat()
    })




























    # services/realtime/connection_manager.py
"""
WebSocket connection manager for real-time communication.
Handles WebSocket connections, disconnections, and message broadcasting.
"""

from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    DOCUMENT_UPDATE = "document_update"
    USER_PRESENCE = "user_presence"
    NOTIFICATION = "notification"
    CHAT_MESSAGE = "chat_message"
    SYSTEM_MESSAGE = "system_message"
    ERROR = "error"


class ConnectionState(str, Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


class WebSocketConnection:
    """Represents a single WebSocket connection."""
    
    def __init__(self, websocket: WebSocket, user_id: str, connection_id: str):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_id = connection_id
        self.state = ConnectionState.CONNECTING
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.subscriptions: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
    
    async def send_json(self, data: Dict[str, Any]) -> bool:
        """Send JSON data to the WebSocket."""
        try:
            if self.state == ConnectionState.CONNECTED:
                await self.websocket.send_json(data)
                return True
        except Exception as e:
            logger.error(f"Failed to send message to {self.connection_id}: {e}")
            self.state = ConnectionState.DISCONNECTED
        return False
    
    async def send_text(self, text: str) -> bool:
        """Send text data to the WebSocket."""
        try:
            if self.state == ConnectionState.CONNECTED:
                await self.websocket.send_text(text)
                return True
        except Exception as e:
            logger.error(f"Failed to send text to {self.connection_id}: {e}")
            self.state = ConnectionState.DISCONNECTED
        return False
    
    def update_heartbeat(self):
        """Update last heartbeat timestamp."""
        self.last_heartbeat = datetime.utcnow()
    
    def is_alive(self, timeout_seconds: int = 60) -> bool:
        """Check if connection is still alive based on heartbeat."""
        time_since_heartbeat = (datetime.utcnow() - self.last_heartbeat).total_seconds()
        return time_since_heartbeat < timeout_seconds


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        # Connection storage
        self._connections: Dict[str, WebSocketConnection] = {}
        self._user_connections: Dict[str, Set[str]] = {}
        self._room_connections: Dict[str, Set[str]] = {}
        
        # Configuration
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 60   # seconds
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start background tasks."""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("ConnectionManager started")
    
    async def stop(self):
        """Stop background tasks."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Close all connections
        for connection in list(self._connections.values()):
            await self.disconnect(connection.connection_id)
        
        logger.info("ConnectionManager stopped")
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        connection_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WebSocketConnection:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket instance
            user_id: ID of the connecting user
            connection_id: Unique connection ID
            metadata: Optional connection metadata
            
        Returns:
            WebSocketConnection instance
        """
        await websocket.accept()
        
        # Create connection
        connection = WebSocketConnection(websocket, user_id, connection_id)
        connection.state = ConnectionState.CONNECTED
        if metadata:
            connection.metadata = metadata
        
        # Store connection
        self._connections[connection_id] = connection
        
        # Track user connections
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(connection_id)
        
        # Send welcome message
        await connection.send_json({
            "type": MessageType.CONNECT,
            "data": {
                "connection_id": connection_id,
                "user_id": user_id,
                "connected_at": connection.connected_at.isoformat(),
                "server_time": datetime.utcnow().isoformat()
            }
        })
        
        logger.info(f"User {user_id} connected with connection {connection_id}")
        
        # Broadcast user presence
        await self.broadcast_user_presence(user_id, "online")
        
        return connection
    
    async def disconnect(self, connection_id: str):
        """
        Disconnect a WebSocket connection.
        
        Args:
            connection_id: ID of the connection to disconnect
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return
        
        # Update state
        connection.state = ConnectionState.DISCONNECTING
        
        # Remove from rooms
        for room_id in list(connection.subscriptions):
            await self.leave_room(connection_id, room_id)
        
        # Remove from user connections
        if connection.user_id in self._user_connections:
            self._user_connections[connection.user_id].discard(connection_id)
            if not self._user_connections[connection.user_id]:
                del self._user_connections[connection.user_id]
                # Broadcast user offline if no more connections
                await self.broadcast_user_presence(connection.user_id, "offline")
        
        # Close WebSocket
        try:
            await connection.websocket.close()
        except Exception as e:
            logger.error(f"Error closing WebSocket {connection_id}: {e}")
        
        # Remove connection
        del self._connections[connection_id]
        
        logger.info(f"Connection {connection_id} disconnected")
    
    async def join_room(self, connection_id: str, room_id: str):
        """
        Add a connection to a room for targeted broadcasting.
        
        Args:
            connection_id: ID of the connection
            room_id: ID of the room to join
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return
        
        # Add to room
        if room_id not in self._room_connections:
            self._room_connections[room_id] = set()
        self._room_connections[room_id].add(connection_id)
        
        # Track subscription
        connection.subscriptions.add(room_id)
        
        logger.info(f"Connection {connection_id} joined room {room_id}")
    
    async def leave_room(self, connection_id: str, room_id: str):
        """
        Remove a connection from a room.
        
        Args:
            connection_id: ID of the connection
            room_id: ID of the room to leave
        """
        connection = self._connections.get(connection_id)
        if connection:
            connection.subscriptions.discard(room_id)
        
        if room_id in self._room_connections:
            self._room_connections[room_id].discard(connection_id)
            if not self._room_connections[room_id]:
                del self._room_connections[room_id]
        
        logger.info(f"Connection {connection_id} left room {room_id}")
    
    async def send_to_user(
        self,
        user_id: str,
        message_type: MessageType,
        data: Dict[str, Any]
    ) -> int:
        """
        Send a message to all connections of a specific user.
        
        Args:
            user_id: ID of the target user
            message_type: Type of message
            data: Message data
            
        Returns:
            Number of connections the message was sent to
        """
        connection_ids = self._user_connections.get(user_id, set())
        sent_count = 0
        
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection_id in list(connection_ids):
            connection = self._connections.get(connection_id)
            if connection and await connection.send_json(message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_room(
        self,
        room_id: str,
        message_type: MessageType,
        data: Dict[str, Any],
        exclude_connection: Optional[str] = None
    ) -> int:
        """
        Broadcast a message to all connections in a room.
        
        Args:
            room_id: ID of the room
            message_type: Type of message
            data: Message data
            exclude_connection: Optional connection ID to exclude
            
        Returns:
            Number of connections the message was sent to
        """
        connection_ids = self._room_connections.get(room_id, set())
        sent_count = 0
        
        message = {
            "type": message_type,
            "data": data,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection_id in list(connection_ids):
            if connection_id == exclude_connection:
                continue
            
            connection = self._connections.get(connection_id)
            if connection and await connection.send_json(message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(
        self,
        message_type: MessageType,
        data: Dict[str, Any],
        exclude_connection: Optional[str] = None
    ) -> int:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message_type: Type of message
            data: Message data
            exclude_connection: Optional connection ID to exclude
            
        Returns:
            Number of connections the message was sent to
        """
        sent_count = 0
        
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection_id, connection in list(self._connections.items()):
            if connection_id == exclude_connection:
                continue
            
            if await connection.send_json(message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_user_presence(self, user_id: str, status: str):
        """Broadcast user presence update."""
        await self.broadcast_to_all(
            MessageType.USER_PRESENCE,
            {
                "user_id": user_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """
        Handle incoming WebSocket message.
        
        Args:
            connection_id: ID of the sending connection
            message: The message data
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return
        
        message_type = message.get("type")
        data = message.get("data", {})
        
        # Handle different message types
        if message_type == MessageType.HEARTBEAT:
            connection.update_heartbeat()
            await connection.send_json({
                "type": MessageType.HEARTBEAT,
                "data": {"status": "ok"}
            })
        
        elif message_type == "join_room":
            room_id = data.get("room_id")
            if room_id:
                await self.join_room(connection_id, room_id)
        
        elif message_type == "leave_room":
            room_id = data.get("room_id")
            if room_id:
                await self.leave_room(connection_id, room_id)
        
        elif message_type == MessageType.CHAT_MESSAGE:
            room_id = data.get("room_id")
            if room_id and room_id in connection.subscriptions:
                await self.broadcast_to_room(
                    room_id,
                    MessageType.CHAT_MESSAGE,
                    {
                        "user_id": connection.user_id,
                        "message": data.get("message"),
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    exclude_connection=connection_id
                )
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to all connections."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Send heartbeat to all connections
                dead_connections = []
                
                for connection_id, connection in list(self._connections.items()):
                    if not connection.is_alive(self.heartbeat_timeout):
                        dead_connections.append(connection_id)
                    else:
                        await connection.send_json({
                            "type": MessageType.HEARTBEAT,
                            "data": {"ping": True}
                        })
                
                # Remove dead connections
                for connection_id in dead_connections:
                    logger.warning(f"Connection {connection_id} timed out")
                    await self.disconnect(connection_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    async def _cleanup_loop(self):
        """Periodic cleanup of stale connections and data."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up empty room mappings
                empty_rooms = [
                    room_id for room_id, connections in self._room_connections.items()
                    if not connections
                ]
                for room_id in empty_rooms:
                    del self._room_connections[room_id]
                
                # Log statistics
                logger.info(
                    f"ConnectionManager stats - "
                    f"Connections: {len(self._connections)}, "
                    f"Users: {len(self._user_connections)}, "
                    f"Rooms: {len(self._room_connections)}"
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics."""
        return {
            "total_connections": len(self._connections),
            "unique_users": len(self._user_connections),
            "active_rooms": len(self._room_connections),
            "connections_by_user": {
                user_id: len(connections)
                for user_id, connections in self._user_connections.items()
            },
            "room_sizes": {
                room_id: len(connections)
                for room_id, connections in self._room_connections.items()
            }
        }
    
    def get_user_connections(self, user_id: str) -> List[str]:
        """Get all connection IDs for a user."""
        return list(self._user_connections.get(user_id, set()))
    
    def get_room_connections(self, room_id: str) -> List[str]:
        """Get all connection IDs in a room."""
        return list(self._room_connections.get(room_id, set()))
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if a user has any active connections."""
        return user_id in self._user_connections and len(self._user_connections[user_id]) > 0


# Global connection manager instance
connection_manager = ConnectionManager()


























# services/realtime/broadcaster.py
"""
Real-time event broadcaster service.
Triggers updates when documents are edited or other events occur.
Integrates with Redis Pub/Sub for distributed broadcasting.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
import redis.asyncio as redis

from .connection_manager import connection_manager, MessageType

logger = logging.getLogger(__name__)


class BroadcastEvent(str, Enum):
    """Types of broadcast events."""
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_SHARED = "document.shared"
    
    USER_JOINED = "user.joined"
    USER_LEFT = "user.left"
    USER_UPDATED = "user.updated"
    
    COMMENT_ADDED = "comment.added"
    COMMENT_UPDATED = "comment.updated"
    COMMENT_DELETED = "comment.deleted"
    
    NOTIFICATION_SENT = "notification.sent"
    
    CASE_UPDATED = "case.updated"
    CLIENT_UPDATED = "client.updated"


class RealtimeBroadcaster:
    """Handles real-time event broadcasting across the application."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.channel_prefix = "goldleaves:broadcast:"
        self.event_handlers: Dict[str, List[Callable]] = {}
        self._subscription_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Initialize Redis connection and start listening."""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis_client.pubsub()
            
            # Subscribe to broadcast channel
            await self.pubsub.subscribe(f"{self.channel_prefix}*")
            
            # Start subscription handler
            self._subscription_task = asyncio.create_task(self._subscription_handler())
            
            logger.info("RealtimeBroadcaster started")
            
        except Exception as e:
            logger.error(f"Failed to start RealtimeBroadcaster: {e}")
            raise
    
    async def stop(self):
        """Stop the broadcaster and clean up resources."""
        if self._subscription_task:
            self._subscription_task.cancel()
        
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("RealtimeBroadcaster stopped")
    
    async def _subscription_handler(self):
        """Handle incoming Redis pub/sub messages."""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    await self._handle_redis_message(message)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in subscription handler: {e}")
    
    async def _handle_redis_message(self, message: Dict[str, Any]):
        """Process a message from Redis pub/sub."""
        try:
            channel = message["channel"]
            data = json.loads(message["data"])
            
            # Extract event type from channel
            event_type = channel.replace(self.channel_prefix, "")
            
            # Trigger local handlers
            await self._trigger_handlers(event_type, data)
            
        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")
    
    async def _trigger_handlers(self, event_type: str, data: Dict[str, Any]):
        """Trigger registered event handlers."""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    def on_event(self, event_type: str):
        """Decorator to register event handlers."""
        def decorator(func: Callable):
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(func)
            return func
        return decorator
    
    async def broadcast(
        self,
        event: BroadcastEvent,
        data: Dict[str, Any],
        room_id: Optional[str] = None,
        user_ids: Optional[List[str]] = None
    ):
        """
        Broadcast an event to connected clients.
        
        Args:
            event: The event type
            data: Event data to broadcast
            room_id: Optional room to broadcast to
            user_ids: Optional list of specific user IDs to broadcast to
        """
        # Add metadata
        broadcast_data = {
            "event": event,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "room_id": room_id,
            "user_ids": user_ids
        }
        
        # Publish to Redis for distributed broadcasting
        if self.redis_client:
            channel = f"{self.channel_prefix}{event}"
            await self.redis_client.publish(channel, json.dumps(broadcast_data))
        
        # Local broadcasting via WebSocket
        if room_id:
            await connection_manager.broadcast_to_room(
                room_id,
                MessageType.SYSTEM_MESSAGE,
                broadcast_data
            )
        elif user_ids:
            for user_id in user_ids:
                await connection_manager.send_to_user(
                    user_id,
                    MessageType.SYSTEM_MESSAGE,
                    broadcast_data
                )
        else:
            await connection_manager.broadcast_to_all(
                MessageType.SYSTEM_MESSAGE,
                broadcast_data
            )
    
    # Convenience methods for common broadcasts
    
    async def broadcast_document_update(
        self,
        document_id: str,
        action: str,
        user_id: str,
        changes: Optional[Dict[str, Any]] = None
    ):
        """Broadcast document update event."""
        event_map = {
            "create": BroadcastEvent.DOCUMENT_CREATED,
            "update": BroadcastEvent.DOCUMENT_UPDATED,
            "delete": BroadcastEvent.DOCUMENT_DELETED,
            "share": BroadcastEvent.DOCUMENT_SHARED
        }
        
        event = event_map.get(action, BroadcastEvent.DOCUMENT_UPDATED)
        
        await self.broadcast(
            event,
            {
                "document_id": document_id,
                "user_id": user_id,
                "action": action,
                "changes": changes or {}
            },
            room_id=f"document:{document_id}"
        )
    
    async def broadcast_user_update(
        self,
        user_id: str,
        update_type: str,
        data: Dict[str, Any]
    ):
        """Broadcast user update event."""
        await self.broadcast(
            BroadcastEvent.USER_UPDATED,
            {
                "user_id": user_id,
                "update_type": update_type,
                "data": data
            },
            user_ids=[user_id]
        )
    
    async def broadcast_comment(
        self,
        document_id: str,
        comment_id: str,
        user_id: str,
        action: str,
        content: Optional[str] = None
    ):
        """Broadcast comment event."""
        event_map = {
            "add": BroadcastEvent.COMMENT_ADDED,
            "update": BroadcastEvent.COMMENT_UPDATED,
            "delete": BroadcastEvent.COMMENT_DELETED
        }
        
        event = event_map.get(action, BroadcastEvent.COMMENT_ADDED)
        
        await self.broadcast(
            event,
            {
                "document_id": document_id,
                "comment_id": comment_id,
                "user_id": user_id,
                "action": action,
                "content": content
            },
            room_id=f"document:{document_id}"
        )
    
    async def broadcast_notification(
        self,
        user_id: str,
        notification: Dict[str, Any]
    ):
        """Broadcast notification to specific user."""
        await self.broadcast(
            BroadcastEvent.NOTIFICATION_SENT,
            notification,
            user_ids=[user_id]
        )
    
    async def broadcast_user_presence(
        self,
        user_id: str,
        status: str,
        room_id: Optional[str] = None
    ):
        """Broadcast user presence update."""
        event = BroadcastEvent.USER_JOINED if status == "joined" else BroadcastEvent.USER_LEFT
        
        data = {
            "user_id": user_id,
            "status": status,
            "room_id": room_id
        }
        
        if room_id:
            await self.broadcast(event, data, room_id=room_id)
        else:
            await self.broadcast(event, data)


# Global broadcaster instance
broadcaster = RealtimeBroadcaster()


# Register default event handlers
@broadcaster.on_event(BroadcastEvent.DOCUMENT_UPDATED)
async def handle_document_update(data: Dict[str, Any]):
    """Handle document update events."""
    document_id = data.get("data", {}).get("document_id")
    if document_id:
        # Notify all users viewing the document
        await connection_manager.broadcast_to_room(
            f"document:{document_id}",
            MessageType.DOCUMENT_UPDATE,
            data["data"]
        )


@broadcaster.on_event(BroadcastEvent.NOTIFICATION_SENT)
async def handle_notification(data: Dict[str, Any]):
    """Handle notification events."""
    user_ids = data.get("user_ids", [])
    notification_data = data.get("data", {})
    
    for user_id in user_ids:
        await connection_manager.send_to_user(
            user_id,
            MessageType.NOTIFICATION,
            notification_data
        )























        # services/realtime/presence.py
"""
User presence tracking service.
Tracks which users are active in shared sessions, documents, and rooms.
"""

import asyncio
import logging
from typing import Dict, Set, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import redis.asyncio as redis
import json

logger = logging.getLogger(__name__)


@dataclass
class UserPresence:
    """Represents a user's presence information."""
    user_id: str
    status: str  # online, away, busy, offline
    last_seen: datetime
    current_room: Optional[str] = None
    current_document: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "status": self.status,
            "last_seen": self.last_seen.isoformat(),
            "current_room": self.current_room,
            "current_document": self.current_document,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPresence':
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            status=data["status"],
            last_seen=datetime.fromisoformat(data["last_seen"]),
            current_room=data.get("current_room"),
            current_document=data.get("current_document"),
            metadata=data.get("metadata", {})
        )


@dataclass
class RoomPresence:
    """Tracks presence in a specific room/document."""
    room_id: str
    active_users: Set[str] = field(default_factory=set)
    user_cursors: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    user_selections: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def add_user(self, user_id: str):
        """Add a user to the room."""
        self.active_users.add(user_id)
    
    def remove_user(self, user_id: str):
        """Remove a user from the room."""
        self.active_users.discard(user_id)
        self.user_cursors.pop(user_id, None)
        self.user_selections.pop(user_id, None)
    
    def update_cursor(self, user_id: str, cursor_data: Dict[str, Any]):
        """Update user's cursor position."""
        self.user_cursors[user_id] = {
            **cursor_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def update_selection(self, user_id: str, selection_data: Dict[str, Any]):
        """Update user's text selection."""
        self.user_selections[user_id] = {
            **selection_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "room_id": self.room_id,
            "active_users": list(self.active_users),
            "user_cursors": self.user_cursors,
            "user_selections": self.user_selections,
            "user_count": len(self.active_users)
        }


class PresenceTracker:
    """Tracks user presence across the application."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        
        # In-memory cache
        self._user_presence: Dict[str, UserPresence] = {}
        self._room_presence: Dict[str, RoomPresence] = {}
        
        # Configuration
        self.presence_ttl = 300  # 5 minutes
        self.away_threshold = 180  # 3 minutes
        self.offline_threshold = 600  # 10 minutes
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._sync_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Initialize the presence tracker."""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._sync_task = asyncio.create_task(self._sync_loop())
            
            # Load existing presence data from Redis
            await self._load_from_redis()
            
            logger.info("PresenceTracker started")
            
        except Exception as e:
            logger.error(f"Failed to start PresenceTracker: {e}")
            raise
    
    async def stop(self):
        """Stop the presence tracker."""
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._sync_task:
            self._sync_task.cancel()
        
        # Save to Redis before stopping
        await self._save_to_redis()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("PresenceTracker stopped")
    
    async def update_user_presence(
        self,
        user_id: str,
        status: Optional[str] = None,
        room_id: Optional[str] = None,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserPresence:
        """
        Update a user's presence information.
        
        Args:
            user_id: ID of the user
            status: User status (online, away, busy, offline)
            room_id: Current room/channel
            document_id: Current document being viewed
            metadata: Additional metadata
            
        Returns:
            Updated UserPresence object
        """
        # Get or create presence
        presence = self._user_presence.get(user_id)
        if not presence:
            presence = UserPresence(
                user_id=user_id,
                status=status or "online",
                last_seen=datetime.utcnow()
            )
            self._user_presence[user_id] = presence
        
        # Update fields
        presence.last_seen = datetime.utcnow()
        if status:
            presence.status = status
        if room_id is not None:
            presence.current_room = room_id
        if document_id is not None:
            presence.current_document = document_id
        if metadata:
            presence.metadata.update(metadata)
        
        # Update Redis
        if self.redis_client:
            key = f"presence:user:{user_id}"
            await self.redis_client.setex(
                key,
                self.presence_ttl,
                json.dumps(presence.to_dict())
            )
        
        return presence
    
    async def get_user_presence(self, user_id: str) -> Optional[UserPresence]:
        """Get a user's presence information."""
        # Check memory cache first
        if user_id in self._user_presence:
            return self._user_presence[user_id]
        
        # Check Redis
        if self.redis_client:
            key = f"presence:user:{user_id}"
            data = await self.redis_client.get(key)
            if data:
                presence = UserPresence.from_dict(json.loads(data))
                self._user_presence[user_id] = presence
                return presence
        
        return None
    
    async def get_online_users(self) -> List[UserPresence]:
        """Get all currently online users."""
        online_users = []
        now = datetime.utcnow()
        
        for presence in self._user_presence.values():
            time_since_seen = (now - presence.last_seen).total_seconds()
            if time_since_seen < self.offline_threshold and presence.status != "offline":
                online_users.append(presence)
        
        return online_users
    
    async def join_room(
        self,
        user_id: str,
        room_id: str,
        initial_cursor: Optional[Dict[str, Any]] = None
    ):
        """User joins a room/document."""
        # Update user presence
        await self.update_user_presence(user_id, room_id=room_id)
        
        # Update room presence
        if room_id not in self._room_presence:
            self._room_presence[room_id] = RoomPresence(room_id=room_id)
        
        room = self._room_presence[room_id]
        room.add_user(user_id)
        
        if initial_cursor:
            room.update_cursor(user_id, initial_cursor)
        
        # Update Redis
        if self.redis_client:
            key = f"presence:room:{room_id}"
            await self.redis_client.setex(
                key,
                self.presence_ttl,
                json.dumps(room.to_dict())
            )
        
        logger.info(f"User {user_id} joined room {room_id}")
    
    async def leave_room(self, user_id: str, room_id: str):
        """User leaves a room/document."""
        # Update user presence
        presence = await self.get_user_presence(user_id)
        if presence and presence.current_room == room_id:
            presence.current_room = None
        
        # Update room presence
        if room_id in self._room_presence:
            room = self._room_presence[room_id]
            room.remove_user(user_id)
            
            # Remove room if empty
            if not room.active_users:
                del self._room_presence[room_id]
                if self.redis_client:
                    await self.redis_client.delete(f"presence:room:{room_id}")
            else:
                # Update Redis
                if self.redis_client:
                    key = f"presence:room:{room_id}"
                    await self.redis_client.setex(
                        key,
                        self.presence_ttl,
                        json.dumps(room.to_dict())
                    )
        
        logger.info(f"User {user_id} left room {room_id}")
    
    async def update_cursor(
        self,
        user_id: str,
        room_id: str,
        cursor_data: Dict[str, Any]
    ):
        """Update user's cursor position in a room."""
        if room_id in self._room_presence:
            room = self._room_presence[room_id]
            if user_id in room.active_users:
                room.update_cursor(user_id, cursor_data)
    
    async def update_selection(
        self,
        user_id: str,
        room_id: str,
        selection_data: Dict[str, Any]
    ):
        """Update user's text selection in a room."""
        if room_id in self._room_presence:
            room = self._room_presence[room_id]
            if user_id in room.active_users:
                room.update_selection(user_id, selection_data)
    
    async def get_room_presence(self, room_id: str) -> Optional[RoomPresence]:
        """Get presence information for a room."""
        # Check memory cache first
        if room_id in self._room_presence:
            return self._room_presence[room_id]
        
        # Check Redis
        if self.redis_client:
            key = f"presence:room:{room_id}"
            data = await self.redis_client.get(key)
            if data:
                room_data = json.loads(data)
                room = RoomPresence(
                    room_id=room_data["room_id"],
                    active_users=set(room_data["active_users"]),
                    user_cursors=room_data.get("user_cursors", {}),
                    user_selections=room_data.get("user_selections", {})
                )
                self._room_presence[room_id] = room
                return room
        
        return None
    
    async def _cleanup_loop(self):
        """Periodically clean up stale presence data."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                now = datetime.utcnow()
                stale_users = []
                
                # Update user statuses based on last seen
                for user_id, presence in self._user_presence.items():
                    time_since_seen = (now - presence.last_seen).total_seconds()
                    
                    if time_since_seen > self.offline_threshold:
                        if presence.status != "offline":
                            presence.status = "offline"
                            # Remove from any rooms
                            if presence.current_room:
                                await self.leave_room(user_id, presence.current_room)
                        
                        # Mark for removal if very stale
                        if time_since_seen > self.presence_ttl * 2:
                            stale_users.append(user_id)
                    
                    elif time_since_seen > self.away_threshold and presence.status == "online":
                        presence.status = "away"
                
                # Remove very stale users
                for user_id in stale_users:
                    del self._user_presence[user_id]
                    if self.redis_client:
                        await self.redis_client.delete(f"presence:user:{user_id}")
                
                logger.debug(f"Cleaned up {len(stale_users)} stale user presence records")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _sync_loop(self):
        """Periodically sync with Redis."""
        while True:
            try:
                await asyncio.sleep(30)  # Sync every 30 seconds
                await self._save_to_redis()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
    
    async def _load_from_redis(self):
        """Load presence data from Redis."""
        if not self.redis_client:
            return
        
        try:
            # Load user presence
            user_keys = await self.redis_client.keys("presence:user:*")
            for key in user_keys:
                data = await self.redis_client.get(key)
                if data:
                    presence = UserPresence.from_dict(json.loads(data))
                    self._user_presence[presence.user_id] = presence
            
            # Load room presence
            room_keys = await self.redis_client.keys("presence:room:*")
            for key in room_keys:
                data = await self.redis_client.get(key)
                if data:
                    room_data = json.loads(data)
                    room = RoomPresence(
                        room_id=room_data["room_id"],
                        active_users=set(room_data["active_users"]),
                        user_cursors=room_data.get("user_cursors", {}),
                        user_selections=room_data.get("user_selections", {})
                    )
                    self._room_presence[room.room_id] = room
            
            logger.info(f"Loaded {len(self._user_presence)} users and {len(self._room_presence)} rooms from Redis")
            
        except Exception as e:
            logger.error(f"Error loading from Redis: {e}")
    
    async def _save_to_redis(self):
        """Save presence data to Redis."""
        if not self.redis_client:
            return
        
        try:
            # Save user presence
            for user_id, presence in self._user_presence.items():
                key = f"presence:user:{user_id}"
                await self.redis_client.setex(
                    key,
                    self.presence_ttl,
                    json.dumps(presence.to_dict())
                )
            
            # Save room presence
            for room_id, room in self._room_presence.items():
                key = f"presence:room:{room_id}"
                await self.redis_client.setex(
                    key,
                    self.presence_ttl,
                    json.dumps(room.to_dict())
                )
            
        except Exception as e:
            logger.error(f"Error saving to Redis: {e}")
    
    def get_presence_stats(self) -> Dict[str, Any]:
        """Get presence statistics."""
        now = datetime.utcnow()
        online_count = 0
        away_count = 0
        busy_count = 0
        
        for presence in self._user_presence.values():
            time_since_seen = (now - presence.last_seen).total_seconds()
            if time_since_seen < self.offline_threshold:
                if presence.status == "online":
                    online_count += 1
                elif presence.status == "away":
                    away_count += 1
                elif presence.status == "busy":
                    busy_count += 1
        
        return {
            "total_tracked": len(self._user_presence),
            "online": online_count,
            "away": away_count,
            "busy": busy_count,
            "active_rooms": len(self._room_presence),
            "rooms_with_users": {
                room_id: len(room.active_users)
                for room_id, room in self._room_presence.items()
            }
        }


# Global presence tracker instance
presence_tracker = PresenceTracker()








































# services/frontend_session/session_store.py
"""
Frontend session store service.
Stores frontend state including UI filters, tabs, theme preferences, etc.
Uses Redis or equivalent for persistent storage.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
import redis.asyncio as redis
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Frontend session data structure."""
    user_id: str
    session_id: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    
    # UI State
    active_tab: str = "dashboard"
    active_document_id: Optional[str] = None
    active_case_id: Optional[str] = None
    sidebar_collapsed: bool = False
    
    # Preferences
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    date_format: str = "MM/DD/YYYY"
    notifications_enabled: bool = True
    desktop_notifications: bool = True
    compact_view: bool = False
    
    # Filters and Search
    document_filters: Dict[str, Any] = field(default_factory=dict)
    search_history: List[str] = field(default_factory=list)
    saved_searches: List[Dict[str, Any]] = field(default_factory=list)
    
    # View States
    sort_preferences: Dict[str, Dict[str, str]] = field(default_factory=dict)
    column_preferences: Dict[str, List[str]] = field(default_factory=dict)
    expanded_items: Set[str] = field(default_factory=set)
    
    # Recent Items
    recent_documents: List[str] = field(default_factory=list)
    recent_cases: List[str] = field(default_factory=list)
    recent_clients: List[str] = field(default_factory=list)
    
    # Custom Data
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO format
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["expires_at"] = self.expires_at.isoformat()
        # Convert sets to lists
        data["expanded_items"] = list(self.expanded_items)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create from dictionary."""
        # Convert ISO strings back to datetime
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        # Convert lists back to sets
        data["expanded_items"] = set(data.get("expanded_items", []))
        return cls(**data)


class FrontendSessionStore:
    """Manages frontend session state storage."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.session_ttl = 86400 * 7  # 7 days
        self.max_recent_items = 10
        self.max_search_history = 20
    
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("FrontendSessionStore initialized")
        except Exception as e:
            logger.error(f"Failed to initialize FrontendSessionStore: {e}")
            # Fallback to in-memory storage if Redis unavailable
            self._memory_store: Dict[str, SessionData] = {}
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def create_session(
        self,
        user_id: str,
        session_id: str,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> SessionData:
        """
        Create a new frontend session.
        
        Args:
            user_id: User ID
            session_id: Unique session ID
            initial_data: Optional initial session data
            
        Returns:
            Created SessionData
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=self.session_ttl)
        
        session = SessionData(
            user_id=user_id,
            session_id=session_id,
            created_at=now,
            updated_at=now,
            expires_at=expires_at
        )
        
        # Apply initial data if provided
        if initial_data:
            for key, value in initial_data.items():
                if hasattr(session, key):
                    setattr(session, key, value)
        
        # Save to storage
        await self._save_session(session)
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session
    
    async def get_session(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> Optional[SessionData]:
        """
        Get session data for a user.
        
        Args:
            user_id: User ID
            session_id: Optional specific session ID
            
        Returns:
            SessionData if found, None otherwise
        """
        if session_id:
            key = f"session:{user_id}:{session_id}"
        else:
            # Get the most recent session for the user
            key = await self._get_latest_session_key(user_id)
            if not key:
                return None
        
        return await self._load_session(key)
    
    async def update_session(
        self,
        user_id: str,
        updates: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Optional[SessionData]:
        """
        Update session data.
        
        Args:
            user_id: User ID
            updates: Dictionary of updates to apply
            session_id: Optional specific session ID
            
        Returns:
            Updated SessionData if found, None otherwise
        """
        session = await self.get_session(user_id, session_id)
        if not session:
            return None
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.updated_at = datetime.utcnow()
        
        # Save updated session
        await self._save_session(session)
        
        return session
    
    async def delete_session(self, user_id: str, session_id: str) -> bool:
        """Delete a specific session."""
        key = f"session:{user_id}:{session_id}"
        
        if self.redis_client:
            result = await self.redis_client.delete(key)
            return result > 0
        else:
            # In-memory fallback
            return self._memory_store.pop(key, None) is not None
    
    async def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from session."""
        session = await self.get_session(user_id)
        if not session:
            return {}
        
        return {
            "theme": session.theme,
            "language": session.language,
            "timezone": session.timezone,
            "date_format": session.date_format,
            "notifications_enabled": session.notifications_enabled,
            "desktop_notifications": session.desktop_notifications,
            "compact_view": session.compact_view,
            "sidebar_collapsed": session.sidebar_collapsed
        }
    
    async def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences."""
        session = await self.update_session(user_id, preferences)
        return session is not None
    
    async def add_recent_item(
        self,
        user_id: str,
        item_type: str,
        item_id: str
    ) -> bool:
        """
        Add item to recent items list.
        
        Args:
            user_id: User ID
            item_type: Type of item (documents, cases, clients)
            item_id: ID of the item
            
        Returns:
            True if successful
        """
        session = await self.get_session(user_id)
        if not session:
            return False
        
        # Get the appropriate list
        list_name = f"recent_{item_type}"
        if not hasattr(session, list_name):
            return False
        
        recent_list = getattr(session, list_name)
        
        # Remove if already exists (to move to front)
        if item_id in recent_list:
            recent_list.remove(item_id)
        
        # Add to front
        recent_list.insert(0, item_id)
        
        # Limit size
        if len(recent_list) > self.max_recent_items:
            recent_list = recent_list[:self.max_recent_items]
            setattr(session, list_name, recent_list)
        
        await self._save_session(session)
        return True
    
    async def add_search_query(self, user_id: str, query: str) -> bool:
        """Add search query to history."""
        session = await self.get_session(user_id)
        if not session:
            return False
        
        # Add to search history
        if query not in session.search_history:
            session.search_history.insert(0, query)
            
            # Limit size
            if len(session.search_history) > self.max_search_history:
                session.search_history = session.search_history[:self.max_search_history]
        
        await self._save_session(session)
        return True
    
    async def save_search(
        self,
        user_id: str,
        name: str,
        query: str,
        filters: Dict[str, Any]
    ) -> bool:
        """Save a search for later use."""
        session = await self.get_session(user_id)
        if not session:
            return False
        
        saved_search = {
            "id": f"search_{datetime.utcnow().timestamp()}",
            "name": name,
            "query": query,
            "filters": filters,
            "created_at": datetime.utcnow().isoformat()
        }
        
        session.saved_searches.append(saved_search)
        
        await self._save_session(session)
        return True
    
    async def get_active_sessions_count(self) -> int:
        """Get count of active sessions."""
        if self.redis_client:
            keys = await self.redis_client.keys("session:*")
            return len(keys)
        else:
            return len(self._memory_store)
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        now = datetime.utcnow()
        cleaned = 0
        
        if self.redis_client:
            # Redis handles expiration automatically with TTL
            # This is just for logging/stats
            keys = await self.redis_client.keys("session:*")
            for key in keys:
                data = await self.redis_client.get(key)
                if data:
                    try:
                        session_dict = json.loads(data)
                        expires_at = datetime.fromisoformat(session_dict["expires_at"])
                        if expires_at < now:
                            await self.redis_client.delete(key)
                            cleaned += 1
                    except Exception:
                        pass
        else:
            # In-memory cleanup
            expired_keys = []
            for key, session in self._memory_store.items():
                if session.expires_at < now:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._memory_store[key]
                cleaned += 1
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired sessions")
        
        return cleaned
    
    async def _save_session(self, session: SessionData):
        """Save session to storage."""
        key = f"session:{session.user_id}:{session.session_id}"
        data = json.dumps(session.to_dict())
        
        if self.redis_client:
            await self.redis_client.setex(
                key,
                self.session_ttl,
                data
            )
            # Also update user's latest session key
            await self.redis_client.setex(
                f"latest_session:{session.user_id}",
                self.session_ttl,
                session.session_id
            )
        else:
            # In-memory fallback
            self._memory_store[key] = session
    
    async def _load_session(self, key: str) -> Optional[SessionData]:
        """Load session from storage."""
        if self.redis_client:
            data = await self.redis_client.get(key)
            if data:
                try:
                    session_dict = json.loads(data)
                    return SessionData.from_dict(session_dict)
                except Exception as e:
                    logger.error(f"Failed to load session {key}: {e}")
        else:
            # In-memory fallback
            return self._memory_store.get(key)
        
        return None
    
    async def _get_latest_session_key(self, user_id: str) -> Optional[str]:
        """Get the latest session key for a user."""
        if self.redis_client:
            session_id = await self.redis_client.get(f"latest_session:{user_id}")
            if session_id:
                return f"session:{user_id}:{session_id}"
        else:
            # In-memory fallback - find most recent
            user_sessions = [
                (key, session) for key, session in self._memory_store.items()
                if session.user_id == user_id
            ]
            if user_sessions:
                # Sort by updated_at descending
                user_sessions.sort(key=lambda x: x[1].updated_at, reverse=True)
                return user_sessions[0][0]
        
        return None





















        # services/frontend_session/activity_tracker.py
"""
Activity tracker service.
Records user actions, last seen documents, and provides analytics.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import redis.asyncio as redis
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ActivityType(str, Enum):
    """Types of user activities to track."""
    # Document activities
    DOCUMENT_VIEWED = "document.viewed"
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_EDITED = "document.edited"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_SHARED = "document.shared"
    DOCUMENT_DOWNLOADED = "document.downloaded"
    
    # Navigation activities
    PAGE_VIEWED = "page.viewed"
    TAB_SWITCHED = "tab.switched"
    SEARCH_PERFORMED = "search.performed"
    FILTER_APPLIED = "filter.applied"
    
    # User activities
    LOGIN = "user.login"
    LOGOUT = "user.logout"
    PROFILE_VIEWED = "profile.viewed"
    SETTINGS_CHANGED = "settings.changed"
    
    # Collaboration activities
    COMMENT_ADDED = "comment.added"
    MENTION_CREATED = "mention.created"
    TASK_ASSIGNED = "task.assigned"
    
    # Other activities
    EXPORT_INITIATED = "export.initiated"
    REPORT_GENERATED = "report.generated"
    API_KEY_CREATED = "api_key.created"


@dataclass
class Activity:
    """Represents a single user activity."""
    id: str
    user_id: str
    activity_type: ActivityType
    timestamp: datetime
    metadata: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["activity_type"] = self.activity_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Activity':
        """Create from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["activity_type"] = ActivityType(data["activity_type"])
        return cls(**data)


class ActivityTracker:
    """Tracks and analyzes user activities."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.activity_ttl = 86400 * 30  # 30 days
        self.stats_ttl = 3600  # 1 hour cache for computed stats
        
        # In-memory buffers for batch writing
        self._activity_buffer: List[Activity] = []
        self._buffer_size = 100
    
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("ActivityTracker initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ActivityTracker: {e}")
            # Fallback to in-memory storage
            self._memory_store: List[Activity] = []
    
    async def close(self):
        """Close Redis connection and flush buffer."""
        await self._flush_buffer()
        if self.redis_client:
            await self.redis_client.close()
    
    async def track_activity(
        self,
        user_id: str,
        activity_type: ActivityType,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Activity:
        """
        Track a user activity.
        
        Args:
            user_id: ID of the user
            activity_type: Type of activity
            metadata: Additional activity metadata
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: Frontend session ID
            
        Returns:
            Created Activity object
        """
        activity = Activity(
            id=f"act_{datetime.utcnow().timestamp()}_{user_id}",
            user_id=user_id,
            activity_type=activity_type,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
        
        # Add to buffer
        self._activity_buffer.append(activity)
        
        # Flush if buffer is full
        if len(self._activity_buffer) >= self._buffer_size:
            await self._flush_buffer()
        
        # Update real-time stats
        await self._update_realtime_stats(activity)
        
        logger.debug(f"Tracked activity: {activity_type.value} for user {user_id}")
        return activity
    
    async def get_user_activities(
        self,
        user_id: str,
        activity_types: Optional[List[ActivityType]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Activity]:
        """
        Get activities for a specific user.
        
        Args:
            user_id: User ID
            activity_types: Filter by activity types
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of activities to return
            
        Returns:
            List of activities
        """
        if self.redis_client:
            # Get from Redis
            pattern = f"activity:{user_id}:*"
            keys = await self.redis_client.keys(pattern)
            
            activities = []
            for key in keys:
                data = await self.redis_client.get(key)
                if data:
                    try:
                        activity = Activity.from_dict(json.loads(data))
                        
                        # Apply filters
                        if activity_types and activity.activity_type not in activity_types:
                            continue
                        if start_date and activity.timestamp < start_date:
                            continue
                        if end_date and activity.timestamp > end_date:
                            continue
                        
                        activities.append(activity)
                    except Exception as e:
                        logger.error(f"Failed to parse activity {key}: {e}")
            
            # Sort by timestamp descending
            activities.sort(key=lambda x: x.timestamp, reverse=True)
            return activities[:limit]
        
        else:
            # In-memory fallback
            filtered = [
                act for act in self._memory_store
                if act.user_id == user_id
            ]
            
            # Apply filters
            if activity_types:
                filtered = [act for act in filtered if act.activity_type in activity_types]
            if start_date:
                filtered = [act for act in filtered if act.timestamp >= start_date]
            if end_date:
                filtered = [act for act in filtered if act.timestamp <= end_date]
            
            # Sort and limit
            filtered.sort(key=lambda x: x.timestamp, reverse=True)
            return filtered[:limit]
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get usage statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of user statistics
        """
        # Check cache first
        if self.redis_client:
            cached = await self.redis_client.get(f"stats:user:{user_id}")
            if cached:
                return json.loads(cached)
        
        # Calculate stats
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)
        
        activities = await self.get_user_activities(
            user_id,
            start_date=last_30_days,
            limit=1000
        )
        
        # Count activities by type
        activity_counts = Counter(act.activity_type.value for act in activities)
        
        # Count activities by period
        activities_7d = [act for act in activities if act.timestamp >= last_7_days]
        
        # Get unique documents accessed
        documents_accessed = set()
        for act in activities:
            if act.activity_type in [ActivityType.DOCUMENT_VIEWED, ActivityType.DOCUMENT_EDITED]:
                doc_id = act.metadata.get("document_id")
                if doc_id:
                    documents_accessed.add(doc_id)
        
        stats = {
            "documents_created": activity_counts.get(ActivityType.DOCUMENT_CREATED.value, 0),
            "documents_edited": activity_counts.get(ActivityType.DOCUMENT_EDITED.value, 0),
            "documents_viewed": activity_counts.get(ActivityType.DOCUMENT_VIEWED.value, 0),
            "documents_accessed_30d": len(documents_accessed),
            "total_activities_30d": len(activities),
            "total_activities_7d": len(activities_7d),
            "searches_performed": activity_counts.get(ActivityType.SEARCH_PERFORMED.value, 0),
            "logins_30d": activity_counts.get(ActivityType.LOGIN.value, 0),
            "last_activity": activities[0].timestamp.isoformat() if activities else None,
            "activity_breakdown": dict(activity_counts),
            "cases_handled": 0,  # Would be calculated from case activities
            "clients_managed": 0,  # Would be calculated from client activities
            "storage_used_mb": 0.0,  # Would be calculated from document sizes
            "storage_limit_mb": 1000.0  # Would come from user plan
        }
        
        # Cache stats
        if self.redis_client:
            await self.redis_client.setex(
                f"stats:user:{user_id}",
                self.stats_ttl,
                json.dumps(stats)
            )
        
        return stats
    
    async def get_popular_documents(
        self,
        organization_id: Optional[str] = None,
        days: int = 7,
        limit: int = 10
    ) -> List[Tuple[str, int]]:
        """
        Get most popular documents by view count.
        
        Args:
            organization_id: Optional organization filter
            days: Number of days to look back
            limit: Number of documents to return
            
        Returns:
            List of (document_id, view_count) tuples
        """
        if self.redis_client:
            # Use Redis sorted set for efficient tracking
            key = f"popular_docs:{organization_id or 'global'}:{days}d"
            results = await self.redis_client.zrevrange(key, 0, limit - 1, withscores=True)
            return [(doc_id, int(score)) for doc_id, score in results]
        
        # In-memory fallback
        start_date = datetime.utcnow() - timedelta(days=days)
        doc_views = Counter()
        
        for activity in self._memory_store:
            if activity.activity_type == ActivityType.DOCUMENT_VIEWED:
                if activity.timestamp >= start_date:
                    doc_id = activity.metadata.get("document_id")
                    if doc_id:
                        doc_views[doc_id] += 1
        
        return doc_views.most_common(limit)
    
    async def get_activity_timeline(
        self,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        hours: int = 24,
        interval_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Get activity timeline with counts per interval.
        
        Args:
            user_id: Optional user filter
            organization_id: Optional organization filter
            hours: Number of hours to look back
            interval_minutes: Interval size in minutes
            
        Returns:
            List of timeline data points
        """
        now = datetime.utcnow()
        start_time = now - timedelta(hours=hours)
        
        # Initialize timeline buckets
        timeline = []
        current_time = start_time
        
        while current_time < now:
            timeline.append({
                "timestamp": current_time.isoformat(),
                "count": 0,
                "types": Counter()
            })
            current_time += timedelta(minutes=interval_minutes)
        
        # Get activities
        activities = []
        if user_id:
            activities = await self.get_user_activities(
                user_id,
                start_date=start_time,
                limit=10000
            )
        elif self.redis_client:
            # Get all activities for organization
            # This would need organization tracking in activities
            pass
        
        # Bucket activities
        for activity in activities:
            # Find the appropriate bucket
            bucket_index = int(
                (activity.timestamp - start_time).total_seconds() / (interval_minutes * 60)
            )
            if 0 <= bucket_index < len(timeline):
                timeline[bucket_index]["count"] += 1
                timeline[bucket_index]["types"][activity.activity_type.value] += 1
        
        # Convert counters to dicts
        for point in timeline:
            point["types"] = dict(point["types"])
        
        return timeline
    
    async def get_search_trends(
        self,
        organization_id: Optional[str] = None,
        days: int = 7,
        limit: int = 20
    ) -> List[Tuple[str, int]]:
        """
        Get trending search queries.
        
        Args:
            organization_id: Optional organization filter
            days: Number of days to look back
            limit: Number of queries to return
            
        Returns:
            List of (query, count) tuples
        """
        if self.redis_client:
            # Use Redis sorted set
            key = f"search_trends:{organization_id or 'global'}:{days}d"
            results = await self.redis_client.zrevrange(key, 0, limit - 1, withscores=True)
            return [(query, int(score)) for query, score in results]
        
        # In-memory fallback
        start_date = datetime.utcnow() - timedelta(days=days)
        search_counts = Counter()
        
        for activity in self._memory_store:
            if activity.activity_type == ActivityType.SEARCH_PERFORMED:
                if activity.timestamp >= start_date:
                    query = activity.metadata.get("query")
                    if query:
                        search_counts[query] += 1
        
        return search_counts.most_common(limit)
    
    async def _flush_buffer(self):
        """Flush activity buffer to storage."""
        if not self._activity_buffer:
            return
        
        if self.redis_client:
            # Batch write to Redis
            pipeline = self.redis_client.pipeline()
            
            for activity in self._activity_buffer:
                key = f"activity:{activity.user_id}:{activity.id}"
                pipeline.setex(
                    key,
                    self.activity_ttl,
                    json.dumps(activity.to_dict())
                )
                
                # Update indexes
                # Daily activity set
                date_key = activity.timestamp.strftime("%Y-%m-%d")
                pipeline.sadd(f"activities:date:{date_key}", activity.id)
                
                # User activity list
                pipeline.lpush(f"activities:user:{activity.user_id}", activity.id)
                pipeline.ltrim(f"activities:user:{activity.user_id}", 0, 999)  # Keep last 1000
                
                # Activity type index
                pipeline.sadd(f"activities:type:{activity.activity_type.value}", activity.id)
            
            await pipeline.execute()
            logger.debug(f"Flushed {len(self._activity_buffer)} activities to Redis")
        
        else:
            # In-memory fallback
            self._memory_store.extend(self._activity_buffer)
            # Keep memory bounded
            if len(self._memory_store) > 10000:
                self._memory_store = self._memory_store[-10000:]
        
        self._activity_buffer.clear()
    
    async def _update_realtime_stats(self, activity: Activity):
        """Update real-time statistics based on activity."""
        if not self.redis_client:
            return
        
        now = datetime.utcnow()
        
        # Update counters
        pipeline = self.redis_client.pipeline()
        
        # Hourly counter
        hour_key = now.strftime("%Y-%m-%d-%H")
        pipeline.hincrby(f"stats:hourly:{hour_key}", activity.activity_type.value, 1)
        pipeline.expire(f"stats:hourly:{hour_key}", 86400 * 2)  # Keep for 2 days
        
        # Daily counter
        day_key = now.strftime("%Y-%m-%d")
        pipeline.hincrby(f"stats:daily:{day_key}", activity.activity_type.value, 1)
        pipeline.expire(f"stats:daily:{day_key}", 86400 * 90)  # Keep for 90 days
        
        # User daily active
        pipeline.sadd(f"active_users:{day_key}", activity.user_id)
        pipeline.expire(f"active_users:{day_key}", 86400 * 30)  # Keep for 30 days
        
        # Document popularity
        if activity.activity_type == ActivityType.DOCUMENT_VIEWED:
            doc_id = activity.metadata.get("document_id")
            if doc_id:
                # 7-day popularity
                pipeline.zincrby(f"popular_docs:global:7d", 1, doc_id)
                pipeline.expire(f"popular_docs:global:7d", 86400 * 7)
                
                # 30-day popularity
                pipeline.zincrby(f"popular_docs:global:30d", 1, doc_id)
                pipeline.expire(f"popular_docs:global:30d", 86400 * 30)
        
        # Search trends
        if activity.activity_type == ActivityType.SEARCH_PERFORMED:
            query = activity.metadata.get("query")
            if query:
                # 7-day trends
                pipeline.zincrby(f"search_trends:global:7d", 1, query.lower())
                pipeline.expire(f"search_trends:global:7d", 86400 * 7)
                
                # 30-day trends
                pipeline.zincrby(f"search_trends:global:30d", 1, query.lower())
                pipeline.expire(f"search_trends:global:30d", 86400 * 30)
        
        await pipeline.execute()
    
    async def get_activity_summary(
        self,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get activity summary for dashboard.
        
        Args:
            user_id: Optional user filter
            organization_id: Optional organization filter
            days: Number of days to summarize
            
        Returns:
            Summary statistics
        """
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)
        
        if self.redis_client:
            # Get from daily stats
            summary = {
                "total_activities": 0,
                "unique_users": set(),
                "activity_breakdown": Counter(),
                "daily_activities": [],
                "peak_hour": None,
                "peak_activity_count": 0
            }
            
            # Collect daily stats
            for i in range(days):
                date = (start_date + timedelta(days=i))
                day_key = date.strftime("%Y-%m-%d")
                
                # Get daily activity counts
                daily_stats = await self.redis_client.hgetall(f"stats:daily:{day_key}")
                daily_total = sum(int(v) for v in daily_stats.values())
                
                summary["daily_activities"].append({
                    "date": day_key,
                    "count": daily_total,
                    "breakdown": daily_stats
                })
                
                summary["total_activities"] += daily_total
                
                for activity_type, count in daily_stats.items():
                    summary["activity_breakdown"][activity_type] += int(count)
                
                # Get unique users
                active_users = await self.redis_client.smembers(f"active_users:{day_key}")
                summary["unique_users"].update(active_users)
                
                # Check hourly stats for peak
                for hour in range(24):
                    hour_key = f"{day_key}-{hour:02d}"
                    hourly_stats = await self.redis_client.hgetall(f"stats:hourly:{hour_key}")
                    hourly_total = sum(int(v) for v in hourly_stats.values())
                    
                    if hourly_total > summary["peak_activity_count"]:
                        summary["peak_activity_count"] = hourly_total
                        summary["peak_hour"] = f"{day_key} {hour:02d}:00"
            
            summary["unique_users"] = len(summary["unique_users"])
            summary["activity_breakdown"] = dict(summary["activity_breakdown"])
            
            return summary
        
        else:
            # In-memory fallback
            activities = []
            if user_id:
                activities = await self.get_user_activities(
                    user_id,
                    start_date=start_date,
                    limit=10000
                )
            
            summary = {
                "total_activities": len(activities),
                "unique_users": len(set(act.user_id for act in activities)),
                "activity_breakdown": dict(Counter(act.activity_type.value for act in activities)),
                "daily_activities": [],
                "peak_hour": None,
                "peak_activity_count": 0
            }
            
            # Group by day
            daily_groups = defaultdict(list)
            for act in activities:
                day_key = act.timestamp.strftime("%Y-%m-%d")
                daily_groups[day_key].append(act)
            
            for day_key, day_activities in sorted(daily_groups.items()):
                summary["daily_activities"].append({
                    "date": day_key,
                    "count": len(day_activities),
                    "breakdown": dict(Counter(act.activity_type.value for act in day_activities))
                })
            
            return summary