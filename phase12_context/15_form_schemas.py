# schemas/forms.py
"""Form-related schemas for Phase 12 crowdsourcing."""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


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
    OTHER = "other"


class FormStatus(str, Enum):
    """Status of form in review process."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class FormLanguage(str, Enum):
    """Supported form languages."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    MANDARIN = "zh"


class ContributorType(str, Enum):
    """Types of contributors."""
    PARALEGAL = "paralegal"
    CROWDSOURCE = "crowdsource"
    MANUAL = "manual"
    ADMIN = "admin"


class FormMetadata(BaseModel):
    """Metadata for uploaded forms."""
    county: Optional[str] = Field(None, description="County where form is used")
    state: Optional[str] = Field(None, description="State where form is used")
    court_type: Optional[str] = Field(None, description="Type of court")
    language: FormLanguage = FormLanguage.ENGLISH
    effective_date: Optional[datetime] = Field(None, description="When form becomes effective")
    expiration_date: Optional[datetime] = Field(None, description="When form expires")
    version: Optional[str] = Field(None, description="Form version")
    source_url: Optional[str] = Field(None, description="Original source URL")
    jurisdiction: Optional[str] = Field(None, description="Legal jurisdiction")


class FormUploadRequest(BaseModel):
    """Request schema for form upload."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    form_type: FormType
    contributor_type: ContributorType = ContributorType.CROWDSOURCE
    metadata: FormMetadata
    tags: Optional[List[str]] = Field(default_factory=list)
    
    @validator('tags')
    def validate_tags(cls, v):
        if v and len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return v


class FormUploadResponse(BaseModel):
    """Response schema for form upload."""
    form_id: str
    title: str
    status: FormStatus = FormStatus.PENDING
    contributor_id: str
    upload_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    estimated_review_time: Optional[str] = "2-3 business days"
    success: bool = True
    message: str = "Form uploaded successfully"


class FormListItem(BaseModel):
    """Form item for list views."""
    form_id: str
    title: str
    form_type: FormType
    status: FormStatus
    contributor_type: ContributorType
    created_at: datetime
    metadata: FormMetadata
    review_score: Optional[float] = Field(None, ge=0, le=10)
    is_approved: bool = False


class FormDetailResponse(BaseModel):
    """Detailed form information."""
    form_id: str
    title: str
    description: Optional[str] = None
    form_type: FormType
    status: FormStatus
    contributor_type: ContributorType
    contributor_id: str
    metadata: FormMetadata
    tags: List[str] = Field(default_factory=list)
    file_info: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_comments: Optional[str] = None
    review_score: Optional[float] = None
    download_count: int = 0
    is_public: bool = False


class FormReviewRequest(BaseModel):
    """Request schema for form review."""
    status: FormStatus
    review_comments: Optional[str] = Field(None, max_length=2000)
    review_score: Optional[float] = Field(None, ge=0, le=10)
    suggested_changes: Optional[List[str]] = Field(default_factory=list)


class FormReviewResponse(BaseModel):
    """Response schema for form review."""
    form_id: str
    status: FormStatus
    reviewed_by: str
    reviewed_at: datetime
    review_comments: Optional[str] = None
    review_score: Optional[float] = None
    success: bool = True
    message: str = "Review completed successfully"


class ContributorReward(BaseModel):
    """Contributor reward information."""
    contributor_id: str
    total_forms_submitted: int = 0
    approved_forms: int = 0
    unique_pages_contributed: int = 0
    free_weeks_earned: int = 0
    current_streak: int = 0
    last_contribution: Optional[datetime] = None


class FormStatsResponse(BaseModel):
    """Form statistics response."""
    total_forms: int = 0
    pending_review: int = 0
    approved_forms: int = 0
    rejected_forms: int = 0
    forms_by_type: Dict[str, int] = Field(default_factory=dict)
    forms_by_language: Dict[str, int] = Field(default_factory=dict)
    top_contributors: List[Dict[str, Any]] = Field(default_factory=list)
    recent_uploads: int = 0


class FeedbackType(str, Enum):
    """Types of feedback."""
    FIELD_ERROR = "field_error"
    PARSING_ISSUE = "parsing_issue"
    JURISDICTION_WRONG = "jurisdiction_wrong"
    CONTENT_ISSUE = "content_issue"
    SUGGESTION = "suggestion"
    COMPLAINT = "complaint"


class FormFeedbackSubmission(BaseModel):
    """User feedback submission."""
    form_id: str
    feedback_type: FeedbackType
    content: str = Field(..., min_length=10, max_length=1000)
    severity: int = Field(1, ge=1, le=5, description="Severity level 1-5")
    contact_email: Optional[str] = Field(None, description="Contact for follow-up")


class FormFeedbackResponse(BaseModel):
    """Response to feedback submission."""
    feedback_id: str
    form_id: str
    status: str = "received"
    ticket_number: Optional[str] = None
    estimated_response_time: str = "2-3 business days"
    success: bool = True
    message: str = "Feedback submitted successfully"
