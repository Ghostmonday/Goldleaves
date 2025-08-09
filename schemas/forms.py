"""
Phase 12: Form-related schemas for crowdsourcing system
Complete Pydantic schemas for API requests/responses
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


# Enums matching the models
class FormType(str, Enum):
    """Types of legal forms."""
    COURT_FILING = "court_filing"
    CONTRACT = "contract"
    MOTION = "motion"
    PLEADING = "pleading"
    DISCOVERY = "discovery"
    BRIEF = "brief"
    PETITION = "petition"
    APPLICATION = "application"
    NOTICE = "notice"
    SUMMONS = "summons"
    SUBPOENA = "subpoena"
    AFFIDAVIT = "affidavit"
    DECLARATION = "declaration"
    STIPULATION = "stipulation"
    ORDER = "order"
    JUDGMENT = "judgment"
    OTHER = "other"


class FormStatus(str, Enum):
    """Status of form in review process."""
    DRAFT = "draft"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    ARCHIVED = "archived"


class ContributorType(str, Enum):
    """Types of contributors."""
    PARALEGAL = "paralegal"
    ATTORNEY = "attorney"
    CROWDSOURCE = "crowdsource"
    MANUAL = "manual"
    ADMIN = "admin"
    SYSTEM = "system"


class FormLanguage(str, Enum):
    """Supported form languages."""
    ENGLISH = "en"
    SPANISH = "es"
    CHINESE = "zh"
    VIETNAMESE = "vi"
    KOREAN = "ko"
    TAGALOG = "tl"
    RUSSIAN = "ru"
    ARABIC = "ar"
    FRENCH = "fr"
    PORTUGUESE = "pt"


class FeedbackType(str, Enum):
    """Types of feedback."""
    FIELD_ERROR = "field_error"
    PARSING_ISSUE = "parsing_issue"
    JURISDICTION_WRONG = "jurisdiction_wrong"
    CONTENT_ISSUE = "content_issue"
    MISSING_FIELD = "missing_field"
    INCORRECT_FORMAT = "incorrect_format"
    OUTDATED_FORM = "outdated_form"
    TRANSLATION_ERROR = "translation_error"
    INSTRUCTION_UNCLEAR = "instruction_unclear"
    TECHNICAL_ISSUE = "technical_issue"
    SUGGESTION = "suggestion"
    COMPLAINT = "complaint"
    PRAISE = "praise"


class ReviewStatus(str, Enum):
    """Review decision status."""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_REVISION = "request_revision"
    ESCALATE = "escalate"


class FeedbackStatus(str, Enum):
    """Feedback ticket status."""
    RECEIVED = "received"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    WONT_FIX = "wont_fix"
    DUPLICATE = "duplicate"


class Priority(str, Enum):
    """Priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


# Base schemas
class JurisdictionInfo(BaseModel):
    """Jurisdiction information."""
    state: str = Field(..., min_length=2, max_length=2, description="State code (e.g., CA)")
    county: Optional[str] = Field(None, max_length=100, description="County name")
    court_type: Optional[str] = Field(None, max_length=100, description="Type of court")
    court_name: Optional[str] = Field(None, max_length=255, description="Specific court name")
    
    @validator('state')
    def validate_state(cls, v):
        valid_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 
                       'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 
                       'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 
                       'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 
                       'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC']
        if v.upper() not in valid_states:
            raise ValueError('Invalid state code')
        return v.upper()


class FormMetadata(BaseModel):
    """Metadata for uploaded forms."""
    jurisdiction: JurisdictionInfo
    form_number: Optional[str] = Field(None, max_length=50, description="Official form number")
    language: FormLanguage = FormLanguage.ENGLISH
    effective_date: Optional[datetime] = Field(None, description="When form becomes effective")
    expiration_date: Optional[datetime] = Field(None, description="When form expires")
    version: Optional[str] = Field(None, max_length=20, description="Form version")
    source_url: Optional[str] = Field(None, max_length=500, description="Original source URL")
    
    # Additional metadata
    case_types: Optional[List[str]] = Field(default_factory=lambda: [], description="Applicable case types")
    filing_fee: Optional[float] = Field(None, ge=0, description="Filing fee if applicable")
    processing_time: Optional[str] = Field(None, description="Typical processing time")
    required_copies: Optional[int] = Field(None, ge=1, description="Number of copies required")
    related_forms: Optional[List[str]] = Field(default_factory=lambda: [], description="Related form numbers")
    
    @validator('source_url')
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class FormFieldDefinition(BaseModel):
    """Definition of a form field."""
    field_name: str
    field_label: Optional[str] = Field(None, max_length=500)
    field_type: str = Field(..., description="text, number, date, checkbox, select, etc.")
    field_order: int = Field(..., ge=0)
    
    # Field properties
    is_required: bool = False
    is_repeatable: bool = False
    max_length: Optional[int] = Field(None, gt=0)
    min_length: Optional[int] = Field(None, ge=0)
    
    # Field grouping
    section_name: Optional[str] = Field(None, max_length=255)
    group_name: Optional[str] = Field(None, max_length=255)
    
    # Validation and help
    validation_rules: Optional[Dict[str, Any]] = Field(default_factory=lambda: {})
    default_value: Optional[str] = None
    placeholder_text: Optional[str] = None
    help_text: Optional[str] = None
    
    # AI hints
    ai_field_category: Optional[str] = Field(None, description="name, address, date, ssn, etc.")
    
    @validator('field_type')
    def validate_field_type(cls, v):
        valid_types = ['text', 'textarea', 'number', 'date', 'datetime', 'time',
                      'checkbox', 'radio', 'select', 'multiselect', 'file',
                      'email', 'phone', 'url', 'currency', 'percentage']
        if v not in valid_types:
            raise ValueError(f'Invalid field type. Must be one of: {", ".join(valid_types)}')
        return v


# Request schemas
class FormUploadRequest(BaseModel):
    """Request schema for form upload."""
    title: str = Field(..., description="Form title")
    description: Optional[str] = Field(None, description="Form description")
    form_type: FormType
    contributor_type: ContributorType = ContributorType.CROWDSOURCE
    metadata: FormMetadata
    tags: Optional[List[str]] = Field(default_factory=lambda: [], max_items=20)
    fields: Optional[List[FormFieldDefinition]] = Field(default_factory=lambda: [], description="Form field definitions")
    
    @validator('tags')
    def validate_tags(cls, v):
        # Remove duplicates and empty tags
        if v:
            return [*{tag.strip() for tag in v if tag.strip()}]
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Motion for Summary Judgment",
                "description": "Standard motion for summary judgment in California Superior Court",
                "form_type": "motion",
                "contributor_type": "paralegal",
                "metadata": {
                    "jurisdiction": {
                        "state": "CA",
                        "county": "Los Angeles",
                        "court_type": "Superior Court"
                    },
                    "form_number": "CIV-120",
                    "language": "en",
                    "version": "1.0"
                },
                "tags": ["civil", "motion", "summary judgment"]
            }
        }


class FormReviewRequest(BaseModel):
    """Request schema for form review."""
    status: ReviewStatus
    review_score: Optional[float] = Field(None, ge=0, le=10, description="Quality score 0-10")
    review_comments: Optional[str] = Field(None, description="Review comments")
    
    # Detailed review checklist
    accuracy_verified: Optional[bool] = None
    formatting_correct: Optional[bool] = None
    fields_complete: Optional[bool] = None
    metadata_accurate: Optional[bool] = None
    
    # Revision requests
    requested_changes: Optional[List[str]] = Field(default_factory=lambda: [], max_items=10)
    revision_deadline: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "approve",
                "review_score": 8.5,
                "review_comments": "Form is accurate and complete",
                "accuracy_verified": True,
                "formatting_correct": True,
                "fields_complete": True,
                "metadata_accurate": True
            }
        }


class FormFeedbackRequest(BaseModel):
    """Request schema for form feedback."""
    form_id: str
    feedback_type: FeedbackType
    title: Optional[str] = None
    content: str
    severity: int = Field(1, ge=1, le=5, description="Severity level 1-5")
    
    # Optional field-specific feedback
    field_name: Optional[str] = None
    suggested_correction: Optional[str] = None
    
    # Contact information
    contact_email: Optional[EmailStr] = None
    allow_contact: bool = False
    
    @validator('severity')
    def validate_severity(cls, v, values):
        # Critical issues should have high severity
        if 'feedback_type' in values:
            critical_types = ['field_error', 'content_issue', 'jurisdiction_wrong']
            if values['feedback_type'] in critical_types and v < 3:
                raise ValueError('Critical feedback types should have severity >= 3')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "form_id": "form_abc123",
                "feedback_type": "field_error",
                "title": "Date field format incorrect",
                "content": "The date field expects MM/DD/YYYY but the form shows DD/MM/YYYY",
                "severity": 4,
                "field_name": "filing_date",
                "suggested_correction": "Change format to MM/DD/YYYY"
            }
        }


class ContributorRewardRequest(BaseModel):
    """Request schema for manual reward grant (admin)."""
    contributor_id: int
    reward_type: str = Field(..., description="free_week, premium_month, api_credits, etc.")
    reward_amount: int = Field(..., gt=0)
    reason: str
    expires_in_days: Optional[int] = Field(None, gt=0, description="Days until expiration")
    
    class Config:
        schema_extra = {
            "example": {
                "contributor_id": 123,
                "reward_type": "free_week",
                "reward_amount": 2,
                "reason": "Exceptional contribution quality",
                "expires_in_days": 90
            }
        }


# Response schemas
class FormUploadResponse(BaseModel):
    """Response schema for form upload."""
    form_id: str
    title: str
    status: FormStatus = FormStatus.PENDING
    contributor_id: int
    upload_url: Optional[str] = Field(None, description="Presigned URL for file upload")
    expires_at: Optional[datetime] = Field(None, description="URL expiration time")
    estimated_review_time: str = "2-3 business days"
    success: bool = True
    message: str = "Form uploaded successfully"
    
    # Duplicate detection results
    similar_forms: Optional[List[Dict[str, Any]]] = None
    is_potential_duplicate: bool = False


class FormListItem(BaseModel):
    """Form item for list views."""
    form_id: str
    title: str
    form_number: Optional[str] = None
    form_type: FormType
    status: FormStatus
    contributor_type: ContributorType
    contributor_name: Optional[str] = None
    
    # Metadata summary
    language: FormLanguage
    jurisdiction_display: str  # "CA - Los Angeles County"
    version: Optional[str] = None
    
    # Dates and metrics
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    review_score: Optional[float] = None
    download_count: int = 0
    
    # Flags
    is_featured: bool = False
    is_current_version: bool = True
    has_feedback: bool = False


class FormDetailResponse(BaseModel):
    """Detailed form information."""
    form_id: str
    title: str
    description: Optional[str] = None
    form_number: Optional[str] = None
    form_type: FormType
    status: FormStatus
    
    # Contributor information
    contributor_type: ContributorType
    contributor_id: int
    contributor_name: Optional[str] = None
    contributor_tier: Optional[str] = None
    
    # Full metadata
    metadata: FormMetadata
    tags: List[str] = Field(default_factory=lambda: [])
    fields: List[FormFieldDefinition] = Field(default_factory=lambda: [])
    
    # File information
    file_info: Dict[str, Any] = Field(default_factory=lambda: {})
    download_url: Optional[str] = None
    
    # Review information
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_comments: Optional[str] = None
    review_score: Optional[float] = None
    review_checklist: Optional[Dict[str, bool]] = None
    
    # Usage statistics
    view_count: int = 0
    download_count: int = 0
    feedback_count: int = 0
    average_rating: Optional[float] = None
    
    # Quality metrics
    completeness_score: Optional[float] = None
    accuracy_verified: bool = False
    last_verified_date: Optional[datetime] = None
    
    # Related information
    related_forms: List[Dict[str, Any]] = Field(default_factory=lambda: [])
    available_versions: List[Dict[str, Any]] = Field(default_factory=lambda: [])
    available_languages: List[FormLanguage] = Field(default_factory=lambda: [])
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


class FormReviewResponse(BaseModel):
    """Response schema for form review."""
    form_id: str
    status: FormStatus
    reviewed_by: str
    reviewed_at: datetime
    review_score: Optional[float] = None
    review_comments: Optional[str] = None
    
    # Review details
    review_checklist: Optional[Dict[str, bool]] = None
    requested_changes: Optional[List[str]] = None
    revision_deadline: Optional[datetime] = None
    
    # Impact
    contributor_notified: bool = True
    reward_granted: Optional[bool] = None
    reward_details: Optional[Dict[str, Any]] = None
    
    success: bool = True
    message: str = "Review completed successfully"


class ContributorRewardStatus(BaseModel):
    """Contributor reward information."""
    contributor_id: int
    contributor_name: Optional[str] = None
    contributor_tier: str = "bronze"
    
    # Contribution statistics
    total_forms_submitted: int = 0
    approved_forms: int = 0
    rejected_forms: int = 0
    pending_forms: int = 0
    approval_rate: Optional[float] = None
    
    # Reward tracking
    unique_pages_contributed: int = 0
    free_weeks_earned: int = 0
    free_weeks_used: int = 0
    free_weeks_available: int = 0
    
    # Quality metrics
    average_review_score: Optional[float] = None
    current_streak: int = 0
    best_streak: int = 0
    
    # Recent activity
    last_contribution: Optional[datetime] = None
    last_approval: Optional[datetime] = None
    recent_contributions: List[Dict[str, Any]] = Field(default_factory=lambda: [])
    
    # Achievements and milestones
    achievements: List[Dict[str, Any]] = Field(default_factory=lambda: [])
    next_milestone: Optional[Dict[str, Any]] = None
    
    # Active rewards
    active_rewards: List[Dict[str, Any]] = Field(default_factory=lambda: [])


class FormFeedbackResponse(BaseModel):
    """Response to feedback submission."""
    feedback_id: str
    form_id: str
    status: FeedbackStatus = FeedbackStatus.RECEIVED
    ticket_number: str
    priority: Priority = Priority.NORMAL
    
    # Expected response
    estimated_response_time: str = "2-3 business days"
    assigned_to: Optional[str] = None
    
    # Voting
    current_votes: Dict[str, int] = Field(default_factory=lambda: {"up": 0, "down": 0})
    
    success: bool = True
    message: str = "Feedback submitted successfully"


class FormStatsResponse(BaseModel):
    """Form statistics response."""
    # Overall statistics
    total_forms: int = 0
    total_contributors: int = 0
    total_jurisdictions: int = 0
    total_languages: int = 0
    
    # Status breakdown
    status_breakdown: Dict[str, int] = Field(default_factory=lambda: {})
    
    # Form type breakdown
    forms_by_type: Dict[str, int] = Field(default_factory=lambda: {})
    forms_by_language: Dict[str, int] = Field(default_factory=lambda: {})
    forms_by_state: Dict[str, int] = Field(default_factory=lambda: {})
    
    # Contribution statistics
    contributions_today: int = 0
    contributions_this_week: int = 0
    contributions_this_month: int = 0
    
    # Review statistics
    average_review_time: Optional[str] = None
    average_review_score: Optional[float] = None
    pending_reviews: int = 0
    
    # Quality metrics
    overall_accuracy_rate: Optional[float] = None
    feedback_resolution_rate: Optional[float] = None
    average_completeness_score: Optional[float] = None
    
    # Top performers
    top_contributors: List[Dict[str, Any]] = Field(default_factory=lambda: [], description="Top 10 contributors")
    featured_forms: List[Dict[str, Any]] = Field(default_factory=lambda: [], description="Featured high-quality forms")
    
    # Trends
    contribution_trend: List[Dict[str, Any]] = Field(default_factory=lambda: [], description="Last 30 days")
    quality_trend: List[Dict[str, Any]] = Field(default_factory=lambda: [], description="Quality scores over time")


class PaginatedFormResponse(BaseModel):
    """Paginated form list response."""
    forms: List[FormListItem]
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")
    filters_applied: Dict[str, Any] = Field(default_factory=lambda: {})
    sort_by: str = "created_at"
    sort_order: str = "desc"
    
    class Config:
        schema_extra = {
            "example": {
                "forms": [],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total": 100,
                    "total_pages": 5,
                    "has_next": True,
                    "has_prev": False
                },
                "filters_applied": {
                    "form_type": "motion",
                    "status": "approved"
                }
            }
        }


class FeedbackStatsResponse(BaseModel):
    """Feedback statistics response."""
    total_feedback: int = 0
    open_tickets: int = 0
    resolved_tickets: int = 0
    average_resolution_time: Optional[str] = None
    
    # Breakdown by type
    feedback_by_type: Dict[str, int] = Field(default_factory=lambda: {})
    feedback_by_severity: Dict[str, int] = Field(default_factory=lambda: {})
    feedback_by_status: Dict[str, int] = Field(default_factory=lambda: {})
    
    # Quality metrics
    user_satisfaction: Optional[float] = None
    resolution_rate: Optional[float] = None
    
    # Recent activity
    feedback_today: int = 0
    feedback_this_week: int = 0
    trending_issues: List[Dict[str, Any]] = Field(default_factory=lambda: [])
    
    # Top issues
    most_reported_forms: List[Dict[str, Any]] = Field(default_factory=lambda: [])
    most_common_issues: List[Dict[str, Any]] = Field(default_factory=lambda: [])


# Utility schemas for filtering and searching
class FormFilters(BaseModel):
    """Filters for form search."""
    form_type: Optional[FormType] = None
    status: Optional[FormStatus] = None
    language: Optional[FormLanguage] = None
    contributor_type: Optional[ContributorType] = None
    state: Optional[str] = None
    county: Optional[str] = None
    form_number: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_score: Optional[float] = None
    is_featured: Optional[bool] = None
    has_feedback: Optional[bool] = None


class FormSearchRequest(BaseModel):
    """Form search request."""
    query: Optional[str] = Field(None, max_length=255, description="Search query")
    filters: Optional[FormFilters] = None
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "motion summary judgment",
                "filters": {
                    "form_type": "motion",
                    "status": "approved",
                    "state": "CA"
                },
                "sort_by": "review_score",
                "sort_order": "desc",
                "page": 1,
                "per_page": 20
            }
        }
