# models/forms.py
"""
Phase 12: Form Models for Crowdsourcing System
Complete database models for forms, contributors, and rewards
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float, Enum, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from enum import Enum as PyEnum

from core.db.base import Base
from core.db.mixins import TimestampMixin, SoftDeleteMixin


class FormType(str, PyEnum):
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


class FormStatus(str, PyEnum):
    """Status of form in review process."""
    DRAFT = "draft"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    ARCHIVED = "archived"


class ContributorType(str, PyEnum):
    """Types of contributors."""
    PARALEGAL = "paralegal"
    ATTORNEY = "attorney"
    CROWDSOURCE = "crowdsource"
    MANUAL = "manual"
    ADMIN = "admin"
    SYSTEM = "system"


class FormLanguage(str, PyEnum):
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


class Jurisdiction(Base, TimestampMixin):
    """Jurisdiction model for form classification."""
    __tablename__ = "jurisdictions"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    state = Column(String(2), nullable=False, index=True)
    county = Column(String(100), nullable=True, index=True)
    court_type = Column(String(100), nullable=True)
    parent_id = Column(Integer, ForeignKey("jurisdictions.id"), nullable=True)
    
    # Hierarchical relationship
    parent = relationship("Jurisdiction", remote_side=[id], backref="children")
    
    # Form relationships
    forms = relationship("Form", back_populates="jurisdiction")
    
    def __repr__(self):
        return f"<Jurisdiction(code={self.code}, name={self.name})>"


class Form(Base, TimestampMixin, SoftDeleteMixin):
    """Model for uploaded forms."""
    __tablename__ = "forms"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(String(32), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    form_number = Column(String(50), nullable=True, index=True)  # Official form number
    form_type = Column(Enum(FormType), nullable=False, index=True)
    status = Column(Enum(FormStatus), default=FormStatus.PENDING, nullable=False, index=True)
    contributor_type = Column(Enum(ContributorType), default=ContributorType.CROWDSOURCE, nullable=False)
    
    # Version tracking
    version = Column(String(20), nullable=True)
    effective_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    supersedes_form_id = Column(Integer, ForeignKey("forms.id"), nullable=True)
    
    # Relationships
    contributor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    jurisdiction_id = Column(Integer, ForeignKey("jurisdictions.id"), nullable=True, index=True)
    
    contributor = relationship("User", foreign_keys=[contributor_id], back_populates="contributed_forms")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id], back_populates="reviewed_forms")
    organization = relationship("Organization", back_populates="forms")
    jurisdiction = relationship("Jurisdiction", back_populates="forms")
    
    # Form content and metadata
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)
    content_type = Column(String(100), nullable=True)
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    
    # Language support
    language = Column(Enum(FormLanguage), default=FormLanguage.ENGLISH, nullable=False)
    available_languages = Column(JSON, nullable=True)  # List of available translations
    
    # Review information
    reviewed_at = Column(DateTime, nullable=True)
    review_comments = Column(Text, nullable=True)
    review_score = Column(Float, nullable=True)
    review_checklist = Column(JSON, nullable=True)  # Structured review criteria
    
    # Metadata and tags
    metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    custom_fields = Column(JSON, nullable=True)  # Form-specific field definitions
    
    # Usage statistics
    download_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    feedback_count = Column(Integer, default=0, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Quality metrics
    completeness_score = Column(Float, nullable=True)  # 0-100 score
    accuracy_verified = Column(Boolean, default=False, nullable=False)
    last_verified_date = Column(DateTime, nullable=True)
    
    # Relationships to other models
    fields = relationship("FormField", back_populates="form", cascade="all, delete-orphan")
    feedback = relationship("FormFeedback", back_populates="form", cascade="all, delete-orphan")
    rewards = relationship("RewardLedger", back_populates="form")
    versions = relationship("FormVersion", back_populates="form", cascade="all, delete-orphan")
    
    # Composite indexes for performance
    __table_args__ = (
        Index('idx_form_type_status', 'form_type', 'status'),
        Index('idx_contributor_status', 'contributor_id', 'status'),
        Index('idx_created_status', 'created_at', 'status'),
        Index('idx_jurisdiction_type', 'jurisdiction_id', 'form_type'),
        Index('idx_form_number', 'form_number'),
        UniqueConstraint('form_number', 'version', 'jurisdiction_id', name='uq_form_version_jurisdiction'),
    )
    
    @hybrid_property
    def is_current_version(self):
        """Check if this is the current version of the form."""
        return self.expiration_date is None or self.expiration_date > datetime.utcnow()
    
    def lock_form(self):
        """Lock form after approval to prevent modifications."""
        self.status = FormStatus.APPROVED
        self.is_public = True
        
    def __repr__(self):
        return f"<Form(id={self.id}, title='{self.title}', status={self.status.value})>"


class FormField(Base, TimestampMixin):
    """Model for form fields and structure."""
    __tablename__ = "form_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False, index=True)
    field_name = Column(String(255), nullable=False)
    field_label = Column(String(500), nullable=True)
    field_type = Column(String(50), nullable=False)  # text, number, date, checkbox, etc.
    field_order = Column(Integer, nullable=False)
    
    # Field properties
    is_required = Column(Boolean, default=False, nullable=False)
    is_repeatable = Column(Boolean, default=False, nullable=False)
    max_length = Column(Integer, nullable=True)
    min_length = Column(Integer, nullable=True)
    
    # Validation rules
    validation_rules = Column(JSON, nullable=True)
    default_value = Column(String(500), nullable=True)
    placeholder_text = Column(String(500), nullable=True)
    help_text = Column(Text, nullable=True)
    
    # Field grouping
    section_name = Column(String(255), nullable=True)
    group_name = Column(String(255), nullable=True)
    parent_field_id = Column(Integer, ForeignKey("form_fields.id"), nullable=True)
    
    # AI parsing hints
    ai_field_category = Column(String(100), nullable=True)  # name, address, date, etc.
    ai_confidence_score = Column(Float, nullable=True)
    
    # Relationships
    form = relationship("Form", back_populates="fields")
    parent_field = relationship("FormField", remote_side=[id], backref="child_fields")
    
    __table_args__ = (
        Index('idx_form_field_order', 'form_id', 'field_order'),
        Index('idx_field_type', 'field_type'),
    )


class ContributorStats(Base, TimestampMixin):
    """Model for tracking contributor statistics and rewards."""
    __tablename__ = "contributor_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    contributor_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # Contribution statistics
    total_forms_submitted = Column(Integer, default=0, nullable=False)
    approved_forms = Column(Integer, default=0, nullable=False)
    rejected_forms = Column(Integer, default=0, nullable=False)
    pending_forms = Column(Integer, default=0, nullable=False)
    revision_requests = Column(Integer, default=0, nullable=False)
    
    # Page and content metrics
    unique_pages_contributed = Column(Integer, default=0, nullable=False)
    total_pages_submitted = Column(Integer, default=0, nullable=False)
    unique_forms_contributed = Column(Integer, default=0, nullable=False)
    
    # Reward tracking
    free_weeks_earned = Column(Integer, default=0, nullable=False)
    free_weeks_used = Column(Integer, default=0, nullable=False)
    bonus_rewards_earned = Column(Integer, default=0, nullable=False)
    current_streak = Column(Integer, default=0, nullable=False)
    best_streak = Column(Integer, default=0, nullable=False)
    
    # Quality metrics
    average_review_score = Column(Float, nullable=True)
    total_review_scores = Column(Float, default=0, nullable=False)
    review_count = Column(Integer, default=0, nullable=False)
    accuracy_rate = Column(Float, nullable=True)  # Percentage of approved vs submitted
    
    # Engagement metrics
    total_downloads = Column(Integer, default=0, nullable=False)
    total_feedback_received = Column(Integer, default=0, nullable=False)
    helpful_feedback_count = Column(Integer, default=0, nullable=False)
    
    # Contribution patterns
    preferred_form_types = Column(JSON, nullable=True)  # Dict of form_type: count
    preferred_jurisdictions = Column(JSON, nullable=True)  # Dict of jurisdiction: count
    contribution_hours = Column(JSON, nullable=True)  # Hour distribution
    
    # Timestamps
    last_contribution = Column(DateTime, nullable=True)
    last_approval = Column(DateTime, nullable=True)
    last_reward_granted = Column(DateTime, nullable=True)
    streak_start_date = Column(DateTime, nullable=True)
    
    # Tier and achievements
    contributor_tier = Column(String(50), default="bronze", nullable=False)  # bronze, silver, gold, platinum
    achievements = Column(JSON, nullable=True)  # List of earned achievements
    
    # Relationships
    contributor = relationship("User", back_populates="contributor_stats")
    
    def calculate_accuracy_rate(self):
        """Calculate contributor accuracy rate."""
        if self.total_forms_submitted > 0:
            self.accuracy_rate = (self.approved_forms / self.total_forms_submitted) * 100
    
    def update_average_score(self, new_score: float):
        """Update rolling average review score."""
        self.total_review_scores += new_score
        self.review_count += 1
        self.average_review_score = self.total_review_scores / self.review_count
    
    def check_tier_upgrade(self):
        """Check if contributor qualifies for tier upgrade."""
        if self.approved_forms >= 100 and self.average_review_score >= 4.5:
            self.contributor_tier = "platinum"
        elif self.approved_forms >= 50 and self.average_review_score >= 4.0:
            self.contributor_tier = "gold"
        elif self.approved_forms >= 20 and self.average_review_score >= 3.5:
            self.contributor_tier = "silver"
    
    def __repr__(self):
        return f"<ContributorStats(contributor_id={self.contributor_id}, approved={self.approved_forms}, tier={self.contributor_tier})>"


class RewardLedger(Base, TimestampMixin):
    """Model for tracking reward grants and usage."""
    __tablename__ = "reward_ledger"
    
    id = Column(Integer, primary_key=True, index=True)
    ledger_id = Column(String(32), unique=True, nullable=False, index=True)
    contributor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=True)
    
    # Reward details
    reward_type = Column(String(50), nullable=False, index=True)  # "free_week", "premium_month", "api_credits"
    reward_amount = Column(Integer, nullable=False)
    reward_value = Column(Float, nullable=True)  # Monetary value if applicable
    reason = Column(String(500), nullable=True)
    
    # Milestone tracking
    milestone_type = Column(String(50), nullable=True)  # "10_pages", "50_forms", "streak_bonus"
    milestone_value = Column(Integer, nullable=True)
    
    # Usage tracking
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    used_at = Column(DateTime, nullable=True)
    
    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    is_expired = Column(Boolean, default=False, nullable=False)
    is_transferable = Column(Boolean, default=False, nullable=False)
    
    # Admin tracking
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    revoked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(String(500), nullable=True)
    
    # Relationships
    contributor = relationship("User", foreign_keys=[contributor_id], back_populates="rewards_earned")
    form = relationship("Form", back_populates="rewards")
    granted_by = relationship("User", foreign_keys=[granted_by_id])
    revoked_by = relationship("User", foreign_keys=[revoked_by_id])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_contributor_active', 'contributor_id', 'is_active'),
        Index('idx_expires_active', 'expires_at', 'is_active'),
        Index('idx_reward_type_active', 'reward_type', 'is_active'),
    )
    
    def activate(self):
        """Activate the reward."""
        self.activated_at = datetime.utcnow()
        self.is_active = True
        
    def use(self):
        """Mark reward as used."""
        self.used_at = datetime.utcnow()
        self.is_used = True
        self.is_active = False
        
    def check_expiration(self):
        """Check if reward has expired."""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            self.is_expired = True
            self.is_active = False
            return True
        return False
    
    def __repr__(self):
        return f"<RewardLedger(contributor_id={self.contributor_id}, type={self.reward_type}, amount={self.reward_amount})>"


class FormFeedback(Base, TimestampMixin):
    """Model for user feedback on forms."""
    __tablename__ = "form_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(32), unique=True, index=True, nullable=False)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Feedback categorization
    feedback_type = Column(String(50), nullable=False, index=True)
    feedback_category = Column(String(50), nullable=True)  # "content", "formatting", "fields", "instructions"
    
    # Feedback content
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    severity = Column(Integer, default=1, nullable=False)  # 1-5 scale
    
    # Specific field feedback
    field_id = Column(Integer, ForeignKey("form_fields.id"), nullable=True)
    field_name = Column(String(255), nullable=True)
    suggested_correction = Column(Text, nullable=True)
    
    # Contact and tracking
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    ticket_number = Column(String(20), unique=True, nullable=True, index=True)
    
    # Status and resolution
    status = Column(String(20), default="received", nullable=False, index=True)
    priority = Column(String(20), default="normal", nullable=True)  # low, normal, high, urgent
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Resolution tracking
    admin_notes = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_type = Column(String(50), nullable=True)  # "fixed", "wont_fix", "duplicate", "invalid"
    
    # Voting and validation
    upvotes = Column(Integer, default=0, nullable=False)
    downvotes = Column(Integer, default=0, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Impact tracking
    forms_affected = Column(Integer, default=1, nullable=False)
    users_affected = Column(Integer, default=1, nullable=False)
    fix_deployed = Column(Boolean, default=False, nullable=False)
    fix_version = Column(String(20), nullable=True)
    
    # Relationships
    form = relationship("Form", back_populates="feedback")
    user = relationship("User", foreign_keys=[user_id], back_populates="feedback_submitted")
    field = relationship("FormField")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_form_feedback_status', 'form_id', 'status'),
        Index('idx_feedback_type_severity', 'feedback_type', 'severity'),
        Index('idx_user_feedback', 'user_id', 'status'),
        Index('idx_priority_status', 'priority', 'status'),
    )
    
    def calculate_impact_score(self):
        """Calculate feedback impact score for prioritization."""
        base_score = self.severity * 20  # 20-100
        vote_score = (self.upvotes - self.downvotes) * 5
        impact_multiplier = min(self.users_affected / 10, 3)  # Cap at 3x
        return int((base_score + vote_score) * impact_multiplier)
    
    def __repr__(self):
        return f"<FormFeedback(form_id={self.form_id}, type={self.feedback_type}, severity={self.severity})>"


class FormVersion(Base, TimestampMixin):
    """Model for tracking form versions."""
    __tablename__ = "form_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False, index=True)
    version_number = Column(String(20), nullable=False)
    
    # Version metadata
    change_summary = Column(Text, nullable=True)
    change_type = Column(String(50), nullable=True)  # "minor", "major", "critical"
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # File tracking
    file_path = Column(String(500), nullable=True)
    file_hash = Column(String(64), nullable=True)
    diff_from_previous = Column(JSON, nullable=True)  # Structured diff data
    
    # Approval for version
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Relationships
    form = relationship("Form", back_populates="versions")
    changed_by = relationship("User", foreign_keys=[changed_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    
    __table_args__ = (
        UniqueConstraint('form_id', 'version_number', name='uq_form_version'),
        Index('idx_form_version', 'form_id', 'created_at'),
    )


# Update User model relationships (add to existing User model)
def update_user_relationships():
    """Add form-related relationships to User model."""
    from models.user import User
    
    # Form relationships
    User.contributed_forms = relationship("Form", foreign_keys="Form.contributor_id", back_populates="contributor")
    User.reviewed_forms = relationship("Form", foreign_keys="Form.reviewed_by_id", back_populates="reviewed_by")
    User.contributor_stats = relationship("ContributorStats", back_populates="contributor", uselist=False)
    User.rewards_earned = relationship("RewardLedger", foreign_keys="RewardLedger.contributor_id", back_populates="contributor")
    User.feedback_submitted = relationship("FormFeedback", foreign_keys="FormFeedback.user_id", back_populates="user")
    
    # Organization relationships
    from models.user import Organization
    Organization.forms = relationship("Form", back_populates="organization")






























# schemas/forms.py
"""
Phase 12: Form-related schemas for crowdsourcing system
Complete Pydantic schemas for API requests/responses
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, constr, EmailStr
from datetime import datetime
from enum import Enum


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
    case_types: Optional[List[str]] = Field(default_factory=list, description="Applicable case types")
    filing_fee: Optional[float] = Field(None, ge=0, description="Filing fee if applicable")
    processing_time: Optional[str] = Field(None, description="Typical processing time")
    required_copies: Optional[int] = Field(None, ge=1, description="Number of copies required")
    related_forms: Optional[List[str]] = Field(default_factory=list, description="Related form numbers")
    
    @validator('source_url')
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class FormFieldDefinition(BaseModel):
    """Definition of a form field."""
    field_name: constr(min_length=1, max_length=255)
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
    validation_rules: Optional[Dict[str, Any]] = Field(default_factory=dict)
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
    title: constr(min_length=1, max_length=500) = Field(..., description="Form title")
    description: Optional[constr(max_length=2000)] = Field(None, description="Form description")
    form_type: FormType
    contributor_type: ContributorType = ContributorType.CROWDSOURCE
    metadata: FormMetadata
    tags: Optional[List[constr(max_length=50)]] = Field(default_factory=list, max_items=20)
    fields: Optional[List[FormFieldDefinition]] = Field(default_factory=list, description="Form field definitions")
    
    @validator('tags')
    def validate_tags(cls, v):
        # Remove duplicates and empty tags
        if v:
            return list(set(tag.strip() for tag in v if tag.strip()))
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
    review_comments: Optional[constr(max_length=2000)] = Field(None, description="Review comments")
    
    # Detailed review checklist
    accuracy_verified: Optional[bool] = None
    formatting_correct: Optional[bool] = None
    fields_complete: Optional[bool] = None
    metadata_accurate: Optional[bool] = None
    
    # Revision requests
    requested_changes: Optional[List[str]] = Field(default_factory=list, max_items=10)
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
    title: Optional[constr(max_length=255)] = None
    content: constr(min_length=10, max_length=2000)
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
    reason: constr(max_length=500)
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
    tags: List[str] = Field(default_factory=list)
    fields: List[FormFieldDefinition] = Field(default_factory=list)
    
    # File information
    file_info: Dict[str, Any] = Field(default_factory=dict)
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
    related_forms: List[Dict[str, Any]] = Field(default_factory=list)
    available_versions: List[Dict[str, Any]] = Field(default_factory=list)
    available_languages: List[FormLanguage] = Field(default_factory=list)
    
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
    recent_contributions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Achievements and milestones
    achievements: List[Dict[str, Any]] = Field(default_factory=list)
    next_milestone: Optional[Dict[str, Any]] = None
    
    # Active rewards
    active_rewards: List[Dict[str, Any]] = Field(default_factory=list)


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
    status_breakdown: Dict[str, int] = Field(default_factory=dict)
    
    # Form type breakdown
    forms_by_type: Dict[str, int] = Field(default_factory=dict)
    forms_by_language: Dict[str, int] = Field(default_factory=dict)
    forms_by_state: Dict[str, int] = Field(default_factory=dict)
    
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
    top_contributors: List[Dict[str, Any]] = Field(default_factory=list, description="Top 10 contributors")
    featured_forms: List[Dict[str, Any]] = Field(default_factory=list, description="Featured high-quality forms")
    
    # Trends
    contribution_trend: List[Dict[str, Any]] = Field(default_factory=list, description="Last 30 days")
    quality_trend: List[Dict[str, Any]] = Field(default_factory=list, description="Quality scores over time")


class PaginatedFormResponse(BaseModel):
    """Paginated form list response."""
    forms: List[FormListItem]
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
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
    feedback_by_type: Dict[str, int] = Field(default_factory=dict)
    feedback_by_severity: Dict[str, int] = Field(default_factory=dict)
    feedback_by_status: Dict[str, int] = Field(default_factory=dict)
    
    # Quality metrics
    user_satisfaction: Optional[float] = None
    resolution_rate: Optional[float] = None
    
    # Recent activity
    feedback_today: int = 0
    feedback_this_week: int = 0
    trending_issues: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Top issues
    most_reported_forms: List[Dict[str, Any]] = Field(default_factory=list)
    most_common_issues: List[Dict[str, Any]] = Field(default_factory=list)



















    