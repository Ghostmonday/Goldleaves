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





















# services/forms/form_registry.py
"""
Phase 12: Form Registry Service
Handles form uploads, validation, deduplication, and reward tracking
"""

import hashlib
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.exc import IntegrityError
import difflib
import re

from models.forms import (
    Form, FormField, FormStatus, FormType, ContributorType,
    ContributorStats, RewardLedger, FormFeedback, FormVersion,
    Jurisdiction, FormLanguage
)
from models.user import User
from schemas.forms import (
    FormUploadRequest, FormUploadResponse, FormDetailResponse,
    FormReviewRequest, FormReviewResponse, ContributorRewardStatus,
    FormListItem, PaginatedFormResponse, FormStatsResponse
)
from core.config import settings
from services.storage import StorageService
from services.notifications import NotificationService


class FormRegistryService:
    """Service for managing form registry operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.storage_service = StorageService()
        self.notification_service = NotificationService(db)
        
    async def upload_form(
        self,
        form_data: FormUploadRequest,
        file_data: bytes,
        file_name: str,
        content_type: str,
        user_id: int
    ) -> FormUploadResponse:
        """
        Upload a new form to the registry.
        Handles validation, deduplication, and initial processing.
        """
        try:
            # Validate file type
            if not self._validate_file_type(content_type, file_name):
                raise ValueError("Invalid file type. Only PDF and DOCX files are supported.")
            
            # Calculate file hash for deduplication
            file_hash = self._calculate_file_hash(file_data)
            
            # Check for duplicates
            duplicate_check = await self._check_duplicates(
                form_data, file_hash, file_data
            )
            
            if duplicate_check["is_duplicate"]:
                return FormUploadResponse(
                    form_id="",
                    title=form_data.title,
                    status=FormStatus.REJECTED,
                    contributor_id=user_id,
                    success=False,
                    message="Duplicate form detected",
                    similar_forms=duplicate_check["similar_forms"],
                    is_potential_duplicate=True
                )
            
            # Generate unique form ID
            form_id = self._generate_form_id()
            
            # Get or create jurisdiction
            jurisdiction = await self._get_or_create_jurisdiction(
                form_data.metadata.jurisdiction
            )
            
            # Create form record
            form = Form(
                form_id=form_id,
                title=form_data.title,
                description=form_data.description,
                form_number=form_data.metadata.form_number,
                form_type=form_data.form_type,
                status=FormStatus.PENDING,
                contributor_type=form_data.contributor_type,
                contributor_id=user_id,
                jurisdiction_id=jurisdiction.id if jurisdiction else None,
                file_hash=file_hash,
                file_size=len(file_data),
                content_type=content_type,
                language=form_data.metadata.language,
                version=form_data.metadata.version,
                effective_date=form_data.metadata.effective_date,
                expiration_date=form_data.metadata.expiration_date,
                metadata=form_data.metadata.dict(),
                tags=form_data.tags
            )
            
            # Store file
            file_path = await self.storage_service.store_form_file(
                form_id, file_data, file_name, content_type
            )
            form.file_path = file_path
            
            # Extract page count (mock - would use PDF/DOCX parser)
            form.page_count = await self._extract_page_count(file_data, content_type)
            
            # Add form fields if provided
            if form_data.fields:
                for field_def in form_data.fields:
                    field = FormField(
                        form_id=form.id,
                        field_name=field_def.field_name,
                        field_label=field_def.field_label,
                        field_type=field_def.field_type,
                        field_order=field_def.field_order,
                        is_required=field_def.is_required,
                        is_repeatable=field_def.is_repeatable,
                        max_length=field_def.max_length,
                        min_length=field_def.min_length,
                        section_name=field_def.section_name,
                        group_name=field_def.group_name,
                        validation_rules=field_def.validation_rules,
                        default_value=field_def.default_value,
                        placeholder_text=field_def.placeholder_text,
                        help_text=field_def.help_text,
                        ai_field_category=field_def.ai_field_category
                    )
                    form.fields.append(field)
            
            # Save form
            self.db.add(form)
            self.db.commit()
            self.db.refresh(form)
            
            # Update contributor statistics
            await self._update_contributor_stats(user_id, "submitted")
            
            # Send notification to admins for review
            await self.notification_service.notify_form_pending_review(form)
            
            # Generate presigned URL for direct file access (if needed)
            upload_url = None
            if settings.ENABLE_DIRECT_UPLOAD:
                upload_url = await self.storage_service.generate_upload_url(
                    form_id, expires_in=3600
                )
            
            return FormUploadResponse(
                form_id=form_id,
                title=form.title,
                status=form.status,
                contributor_id=user_id,
                upload_url=upload_url,
                expires_at=datetime.utcnow() + timedelta(hours=1) if upload_url else None,
                similar_forms=duplicate_check.get("similar_forms", [])
            )
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def review_form(
        self,
        form_id: str,
        review_data: FormReviewRequest,
        reviewer_id: int
    ) -> FormReviewResponse:
        """
        Review a submitted form.
        Handles approval, rejection, and revision requests.
        """
        # Get form with relationships
        form = self.db.query(Form).filter(
            Form.form_id == form_id
        ).first()
        
        if not form:
            raise ValueError("Form not found")
        
        if form.status != FormStatus.PENDING:
            raise ValueError("Form is not pending review")
        
        # Update review information
        form.reviewed_by_id = reviewer_id
        form.reviewed_at = datetime.utcnow()
        form.review_comments = review_data.review_comments
        form.review_score = review_data.review_score
        
        # Create review checklist
        review_checklist = {
            "accuracy_verified": review_data.accuracy_verified,
            "formatting_correct": review_data.formatting_correct,
            "fields_complete": review_data.fields_complete,
            "metadata_accurate": review_data.metadata_accurate
        }
        form.review_checklist = review_checklist
        
        # Determine new status based on review
        reward_granted = False
        reward_details = None
        
        if review_data.status == "approve":
            form.status = FormStatus.APPROVED
            form.is_public = True
            
            # Grant rewards for approved forms
            reward_granted, reward_details = await self._process_approval_rewards(
                form.contributor_id, form.id, form.page_count
            )
            
            # Update contributor stats
            await self._update_contributor_stats(
                form.contributor_id, "approved", review_data.review_score
            )
            
            # Lock form to prevent modifications
            form.lock_form()
            
        elif review_data.status == "reject":
            form.status = FormStatus.REJECTED
            
            # Update contributor stats
            await self._update_contributor_stats(form.contributor_id, "rejected")
            
        elif review_data.status == "request_revision":
            form.status = FormStatus.NEEDS_REVISION
            
            # Store revision requests
            form.metadata["revision_requests"] = review_data.requested_changes
            form.metadata["revision_deadline"] = review_data.revision_deadline.isoformat() if review_data.revision_deadline else None
            
            # Update contributor stats
            await self._update_contributor_stats(form.contributor_id, "revision")
        
        # Save changes
        self.db.commit()
        self.db.refresh(form)
        
        # Get reviewer info
        reviewer = self.db.query(User).filter(User.id == reviewer_id).first()
        
        # Send notification to contributor
        await self.notification_service.notify_form_reviewed(
            form, review_data.status, review_data.review_comments
        )
        
        return FormReviewResponse(
            form_id=form.form_id,
            status=form.status,
            reviewed_by=reviewer.email if reviewer else "Unknown",
            reviewed_at=form.reviewed_at,
            review_score=form.review_score,
            review_comments=form.review_comments,
            review_checklist=review_checklist,
            requested_changes=review_data.requested_changes,
            revision_deadline=review_data.revision_deadline,
            reward_granted=reward_granted,
            reward_details=reward_details
        )
    
    async def get_form_details(
        self,
        form_id: str,
        user_id: Optional[int] = None
    ) -> FormDetailResponse:
        """Get detailed information about a specific form."""
        # Query form with all relationships
        form = self.db.query(Form).options(
            joinedload(Form.contributor),
            joinedload(Form.reviewed_by),
            joinedload(Form.jurisdiction),
            joinedload(Form.fields),
            joinedload(Form.feedback)
        ).filter(Form.form_id == form_id).first()
        
        if not form:
            raise ValueError("Form not found")
        
        # Check access permissions
        if not form.is_public and user_id != form.contributor_id:
            # Check if user is admin
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_admin:
                raise ValueError("Access denied")
        
        # Increment view count
        form.view_count += 1
        self.db.commit()
        
        # Get contributor stats
        contributor_stats = self.db.query(ContributorStats).filter(
            ContributorStats.contributor_id == form.contributor_id
        ).first()
        
        # Get related forms
        related_forms = await self._get_related_forms(form)
        
        # Get available versions
        available_versions = await self._get_form_versions(form)
        
        # Calculate average rating from feedback
        avg_rating = None
        if form.feedback:
            ratings = [f.severity for f in form.feedback if f.severity]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
        
        # Build file info
        file_info = {
            "file_name": form.file_path.split('/')[-1] if form.file_path else None,
            "file_size": form.file_size,
            "content_type": form.content_type,
            "page_count": form.page_count,
            "upload_date": form.created_at.isoformat()
        }
        
        # Generate download URL if authorized
        download_url = None
        if form.is_public or user_id == form.contributor_id:
            download_url = await self.storage_service.generate_download_url(
                form.file_path, expires_in=3600
            )
        
        # Format jurisdiction display
        jurisdiction_display = ""
        if form.jurisdiction:
            jurisdiction_display = f"{form.jurisdiction.state}"
            if form.jurisdiction.county:
                jurisdiction_display += f" - {form.jurisdiction.county}"
            if form.jurisdiction.court_type:
                jurisdiction_display += f" ({form.jurisdiction.court_type})"
        
        return FormDetailResponse(
            form_id=form.form_id,
            title=form.title,
            description=form.description,
            form_number=form.form_number,
            form_type=form.form_type,
            status=form.status,
            contributor_type=form.contributor_type,
            contributor_id=form.contributor_id,
            contributor_name=form.contributor.email if form.contributor else None,
            contributor_tier=contributor_stats.contributor_tier if contributor_stats else "bronze",
            metadata=form.metadata,
            tags=form.tags or [],
            fields=[self._field_to_dict(f) for f in form.fields],
            file_info=file_info,
            download_url=download_url,
            reviewed_at=form.reviewed_at,
            reviewed_by=form.reviewed_by.email if form.reviewed_by else None,
            review_comments=form.review_comments,
            review_score=form.review_score,
            review_checklist=form.review_checklist,
            view_count=form.view_count,
            download_count=form.download_count,
            feedback_count=len(form.feedback) if form.feedback else 0,
            average_rating=avg_rating,
            completeness_score=form.completeness_score,
            accuracy_verified=form.accuracy_verified,
            last_verified_date=form.last_verified_date,
            related_forms=related_forms,
            available_versions=available_versions,
            available_languages=[form.language],  # TODO: Add translation support
            created_at=form.created_at,
            updated_at=form.updated_at
        )
    
    async def list_forms(
        self,
        page: int = 1,
        per_page: int = 20,
        form_type: Optional[FormType] = None,
        status: Optional[FormStatus] = None,
        contributor_id: Optional[int] = None,
        jurisdiction_id: Optional[int] = None,
        language: Optional[FormLanguage] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PaginatedFormResponse:
        """Get paginated list of forms with filters."""
        # Build query
        query = self.db.query(Form).options(
            joinedload(Form.contributor),
            joinedload(Form.jurisdiction)
        )
        
        # Apply filters
        filters_applied = {}
        
        if form_type:
            query = query.filter(Form.form_type == form_type)
            filters_applied["form_type"] = form_type
            
        if status:
            query = query.filter(Form.status == status)
            filters_applied["status"] = status
            
        if contributor_id:
            query = query.filter(Form.contributor_id == contributor_id)
            filters_applied["contributor_id"] = contributor_id
            
        if jurisdiction_id:
            query = query.filter(Form.jurisdiction_id == jurisdiction_id)
            filters_applied["jurisdiction_id"] = jurisdiction_id
            
        if language:
            query = query.filter(Form.language == language)
            filters_applied["language"] = language
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Form.title.ilike(search_term),
                    Form.description.ilike(search_term),
                    Form.form_number.ilike(search_term),
                    Form.tags.contains([search])
                )
            )
            filters_applied["search"] = search
        
        # Apply sorting
        if sort_by == "created_at":
            order_col = Form.created_at
        elif sort_by == "title":
            order_col = Form.title
        elif sort_by == "review_score":
            order_col = Form.review_score
        elif sort_by == "download_count":
            order_col = Form.download_count
        else:
            order_col = Form.created_at
            
        if sort_order == "desc":
            query = query.order_by(desc(order_col))
        else:
            query = query.order_by(order_col)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        forms = query.offset(offset).limit(per_page).all()
        
        # Convert to response format
        form_items = []
        for form in forms:
            # Get contributor stats for tier
            contributor_stats = self.db.query(ContributorStats).filter(
                ContributorStats.contributor_id == form.contributor_id
            ).first()
            
            # Format jurisdiction display
            jurisdiction_display = ""
            if form.jurisdiction:
                jurisdiction_display = f"{form.jurisdiction.state}"
                if form.jurisdiction.county:
                    jurisdiction_display += f" - {form.jurisdiction.county}"
            
            # Check for feedback
            has_feedback = self.db.query(FormFeedback).filter(
                FormFeedback.form_id == form.id
            ).count() > 0
            
            form_items.append(FormListItem(
                form_id=form.form_id,
                title=form.title,
                form_number=form.form_number,
                form_type=form.form_type,
                status=form.status,
                contributor_type=form.contributor_type,
                contributor_name=form.contributor.email if form.contributor else None,
                language=form.language,
                jurisdiction_display=jurisdiction_display,
                version=form.version,
                created_at=form.created_at,
                reviewed_at=form.reviewed_at,
                review_score=form.review_score,
                download_count=form.download_count,
                is_featured=form.is_featured,
                is_current_version=form.is_current_version,
                has_feedback=has_feedback
            ))
        
        # Calculate pagination metadata
        total_pages = (total + per_page - 1) // per_page
        
        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return PaginatedFormResponse(
            forms=form_items,
            pagination=pagination,
            filters_applied=filters_applied,
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    async def get_contributor_rewards(
        self,
        contributor_id: int
    ) -> ContributorRewardStatus:
        """Get contributor reward information."""
        # Get contributor stats
        stats = self.db.query(ContributorStats).filter(
            ContributorStats.contributor_id == contributor_id
        ).first()
        
        if not stats:
            # Create initial stats record
            stats = ContributorStats(contributor_id=contributor_id)
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(stats)
        
        # Get contributor info
        contributor = self.db.query(User).filter(
            User.id == contributor_id
        ).first()
        
        # Calculate approval rate
        approval_rate = None
        if stats.total_forms_submitted > 0:
            approval_rate = (stats.approved_forms / stats.total_forms_submitted) * 100
        
        # Get recent contributions
        recent_forms = self.db.query(Form).filter(
            Form.contributor_id == contributor_id
        ).order_by(desc(Form.created_at)).limit(5).all()
        
        recent_contributions = [
            {
                "form_id": form.form_id,
                "title": form.title,
                "status": form.status.value,
                "created_at": form.created_at.isoformat(),
                "review_score": form.review_score
            }
            for form in recent_forms
        ]
        
        # Get active rewards
        active_rewards = self.db.query(RewardLedger).filter(
            and_(
                RewardLedger.contributor_id == contributor_id,
                RewardLedger.is_active == True,
                or_(
                    RewardLedger.expires_at == None,
                    RewardLedger.expires_at > datetime.utcnow()
                )
            )
        ).all()
        
        active_reward_list = [
            {
                "reward_type": reward.reward_type,
                "reward_amount": reward.reward_amount,
                "granted_at": reward.granted_at.isoformat(),
                "expires_at": reward.expires_at.isoformat() if reward.expires_at else None,
                "reason": reward.reason
            }
            for reward in active_rewards
        ]
        
        # Calculate available free weeks
        free_weeks_available = stats.free_weeks_earned - stats.free_weeks_used
        
        # Get achievements
        achievements = stats.achievements or []
        
        # Calculate next milestone
        next_milestone = self._calculate_next_milestone(stats)
        
        return ContributorRewardStatus(
            contributor_id=contributor_id,
            contributor_name=contributor.email if contributor else None,
            contributor_tier=stats.contributor_tier,
            total_forms_submitted=stats.total_forms_submitted,
            approved_forms=stats.approved_forms,
            rejected_forms=stats.rejected_forms,
            pending_forms=stats.pending_forms,
            approval_rate=approval_rate,
            unique_pages_contributed=stats.unique_pages_contributed,
            free_weeks_earned=stats.free_weeks_earned,
            free_weeks_used=stats.free_weeks_used,
            free_weeks_available=free_weeks_available,
            average_review_score=stats.average_review_score,
            current_streak=stats.current_streak,
            best_streak=stats.best_streak,
            last_contribution=stats.last_contribution,
            last_approval=stats.last_approval,
            recent_contributions=recent_contributions,
            achievements=achievements,
            next_milestone=next_milestone,
            active_rewards=active_reward_list
        )
    
    async def get_form_stats(self) -> FormStatsResponse:
        """Get comprehensive form registry statistics."""
        # Overall counts
        total_forms = self.db.query(Form).filter(
            Form.is_deleted == False
        ).count()
        
        total_contributors = self.db.query(
            func.count(func.distinct(Form.contributor_id))
        ).scalar()
        
        total_jurisdictions = self.db.query(
            func.count(func.distinct(Form.jurisdiction_id))
        ).filter(Form.jurisdiction_id != None).scalar()
        
        total_languages = self.db.query(
            func.count(func.distinct(Form.language))
        ).scalar()
        
        # Status breakdown
        status_breakdown = {}
        status_counts = self.db.query(
            Form.status, func.count(Form.id)
        ).group_by(Form.status).all()
        
        for status, count in status_counts:
            status_breakdown[status.value] = count
        
        # Form type breakdown
        forms_by_type = {}
        type_counts = self.db.query(
            Form.form_type, func.count(Form.id)
        ).group_by(Form.form_type).all()
        
        for form_type, count in type_counts:
            forms_by_type[form_type.value] = count
        
        # Language breakdown
        forms_by_language = {}
        language_counts = self.db.query(
            Form.language, func.count(Form.id)
        ).group_by(Form.language).all()
        
        for language, count in language_counts:
            forms_by_language[language.value] = count
        
        # State breakdown
        forms_by_state = {}
        state_counts = self.db.query(
            Jurisdiction.state, func.count(Form.id)
        ).join(Form.jurisdiction).group_by(Jurisdiction.state).all()
        
        for state, count in state_counts:
            forms_by_state[state] = count
        
        # Contribution statistics
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        contributions_today = self.db.query(Form).filter(
            func.date(Form.created_at) == today
        ).count()
        
        contributions_this_week = self.db.query(Form).filter(
            Form.created_at >= week_ago
        ).count()
        
        contributions_this_month = self.db.query(Form).filter(
            Form.created_at >= month_ago
        ).count()
        
        # Review statistics
        pending_reviews = self.db.query(Form).filter(
            Form.status == FormStatus.PENDING
        ).count()
        
        # Calculate average review time
        reviewed_forms = self.db.query(Form).filter(
            and_(
                Form.reviewed_at != None,
                Form.created_at != None
            )
        ).all()
        
        if reviewed_forms:
            total_review_time = sum(
                (form.reviewed_at - form.created_at).total_seconds() 
                for form in reviewed_forms
            )
            avg_seconds = total_review_time / len(reviewed_forms)
            avg_hours = avg_seconds / 3600
            
            if avg_hours < 24:
                average_review_time = f"{avg_hours:.1f} hours"
            else:
                average_review_time = f"{avg_hours/24:.1f} days"
        else:
            average_review_time = None
        
        # Average review score
        avg_score_result = self.db.query(
            func.avg(Form.review_score)
        ).filter(Form.review_score != None).scalar()
        
        average_review_score = float(avg_score_result) if avg_score_result else None
        
        # Quality metrics
        accuracy_rate_result = self.db.query(
            func.avg(ContributorStats.accuracy_rate)
        ).filter(ContributorStats.accuracy_rate != None).scalar()
        
        overall_accuracy_rate = float(accuracy_rate_result) if accuracy_rate_result else None
        
        # Feedback resolution rate
        total_feedback = self.db.query(FormFeedback).count()
        resolved_feedback = self.db.query(FormFeedback).filter(
            FormFeedback.status.in_(["resolved", "closed", "wont_fix"])
        ).count()
        
        feedback_resolution_rate = (
            (resolved_feedback / total_feedback * 100) if total_feedback > 0 else None
        )
        
        # Top contributors
        top_contributors_query = self.db.query(
            User.id,
            User.email,
            ContributorStats.approved_forms,
            ContributorStats.average_review_score,
            ContributorStats.contributor_tier
        ).join(
            ContributorStats, User.id == ContributorStats.contributor_id
        ).order_by(
            desc(ContributorStats.approved_forms)
        ).limit(10).all()
        
        top_contributors = [
            {
                "contributor_id": c[0],
                "contributor_name": c[1],
                "approved_forms": c[2],
                "average_score": c[3],
                "tier": c[4]
            }
            for c in top_contributors_query
        ]
        
        # Featured forms (highest rated recent forms)
        featured_forms_query = self.db.query(Form).filter(
            and_(
                Form.status == FormStatus.APPROVED,
                Form.review_score != None,
                Form.is_public == True
            )
        ).order_by(
            desc(Form.review_score),
            desc(Form.created_at)
        ).limit(5).all()
        
        featured_forms = [
            {
                "form_id": form.form_id,
                "title": form.title,
                "form_type": form.form_type.value,
                "review_score": form.review_score,
                "download_count": form.download_count
            }
            for form in featured_forms_query
        ]
        
        # Contribution trend (last 30 days)
        contribution_trend = []
        for i in range(30):
            date = today - timedelta(days=i)
            count = self.db.query(Form).filter(
                func.date(Form.created_at) == date
            ).count()
            
            contribution_trend.append({
                "date": date.isoformat(),
                "count": count
            })
        
        contribution_trend.reverse()  # Oldest to newest
        
        return FormStatsResponse(
            total_forms=total_forms,
            total_contributors=total_contributors,
            total_jurisdictions=total_jurisdictions,
            total_languages=total_languages,
            status_breakdown=status_breakdown,
            forms_by_type=forms_by_type,
            forms_by_language=forms_by_language,
            forms_by_state=forms_by_state,
            contributions_today=contributions_today,
            contributions_this_week=contributions_this_week,
            contributions_this_month=contributions_this_month,
            average_review_time=average_review_time,
            average_review_score=average_review_score,
            pending_reviews=pending_reviews,
            overall_accuracy_rate=overall_accuracy_rate,
            feedback_resolution_rate=feedback_resolution_rate,
            top_contributors=top_contributors,
            featured_forms=featured_forms,
            contribution_trend=contribution_trend
        )
    
    # Private helper methods
    
    def _generate_form_id(self) -> str:
        """Generate unique form ID."""
        return f"form_{uuid.uuid4().hex[:12]}"
    
    def _calculate_file_hash(self, file_data: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(file_data).hexdigest()
    
    def _validate_file_type(self, content_type: str, file_name: str) -> bool:
        """Validate uploaded file type."""
        valid_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ]
        
        if content_type in valid_types:
            return True
            
        # Check file extension as fallback
        ext = file_name.lower().split('.')[-1]
        return ext in ['pdf', 'docx', 'doc']
    
    async def _check_duplicates(
        self,
        form_data: FormUploadRequest,
        file_hash: str,
        file_data: bytes
    ) -> Dict[str, Any]:
        """
        Check for duplicate forms using multiple strategies.
        Returns dict with is_duplicate flag and similar forms.
        """
        similar_forms = []
        
        # 1. Exact file hash match
        hash_match = self.db.query(Form).filter(
            Form.file_hash == file_hash
        ).first()
        
        if hash_match:
            return {
                "is_duplicate": True,
                "similar_forms": [{
                    "form_id": hash_match.form_id,
                    "title": hash_match.title,
                    "match_type": "exact_file",
                    "confidence": 100
                }]
            }
        
        # 2. Title similarity check
        existing_forms = self.db.query(Form).filter(
            and_(
                Form.jurisdiction_id == form_data.metadata.jurisdiction.state,
                Form.form_type == form_data.form_type,
                Form.status != FormStatus.REJECTED
            )
        ).all()
        
        for existing in existing_forms:
            # Calculate title similarity
            similarity = difflib.SequenceMatcher(
                None, 
                form_data.title.lower(), 
                existing.title.lower()
            ).ratio()
            
            if similarity > 0.85:  # 85% similarity threshold
                similar_forms.append({
                    "form_id": existing.form_id,
                    "title": existing.title,
                    "match_type": "title_similarity",
                    "confidence": int(similarity * 100)
                })
        
        # 3. Form number match
        if form_data.metadata.form_number:
            form_number_match = self.db.query(Form).filter(
                and_(
                    Form.form_number == form_data.metadata.form_number,
                    Form.jurisdiction_id == form_data.metadata.jurisdiction.state,
                    Form.status == FormStatus.APPROVED
                )
            ).first()
            
            if form_number_match:
                similar_forms.append({
                    "form_id": form_number_match.form_id,
                    "title": form_number_match.title,
                    "match_type": "form_number",
                    "confidence": 95
                })
        
        # Sort by confidence
        similar_forms.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Determine if it's a duplicate
        is_duplicate = any(
            form['confidence'] >= 95 for form in similar_forms
        )
        
        return {
            "is_duplicate": is_duplicate,
            "similar_forms": similar_forms[:5]  # Return top 5 matches
        }
    
    async def _get_or_create_jurisdiction(
        self,
        jurisdiction_info: Dict[str, Any]
    ) -> Optional[Jurisdiction]:
        """Get or create jurisdiction record."""
        if not jurisdiction_info:
            return None
        
        # Look for existing jurisdiction
        existing = self.db.query(Jurisdiction).filter(
            and_(
                Jurisdiction.state == jurisdiction_info['state'],
                Jurisdiction.county == jurisdiction_info.get('county'),
                Jurisdiction.court_type == jurisdiction_info.get('court_type')
            )
        ).first()
        
        if existing:
            return existing
        
        # Create new jurisdiction
        code = f"{jurisdiction_info['state']}"
        if jurisdiction_info.get('county'):
            code += f"-{jurisdiction_info['county'].replace(' ', '_').upper()}"
        
        jurisdiction = Jurisdiction(
            code=code,
            name=jurisdiction_info.get('court_name') or f"{jurisdiction_info['state']} Court",
            state=jurisdiction_info['state'],
            county=jurisdiction_info.get('county'),
            court_type=jurisdiction_info.get('court_type')
        )
        
        self.db.add(jurisdiction)
        self.db.commit()
        self.db.refresh(jurisdiction)
        
        return jurisdiction
    
    async def _extract_page_count(
        self,
        file_data: bytes,
        content_type: str
    ) -> int:
        """Extract page count from PDF or DOCX file."""
        # This would use actual PDF/DOCX parsing libraries
        # For now, return mock value
        return 5
    
    async def _update_contributor_stats(
        self,
        contributor_id: int,
        action: str,
        review_score: Optional[float] = None
    ):
        """Update contributor statistics based on action."""
        stats = self.db.query(ContributorStats).filter(
            ContributorStats.contributor_id == contributor_id
        ).first()
        
        if not stats:
            stats = ContributorStats(contributor_id=contributor_id)
            self.db.add(stats)
        
        if action == "submitted":
            stats.total_forms_submitted += 1
            stats.pending_forms += 1
            stats.last_contribution = datetime.utcnow()
            
            # Update streak
            if stats.last_contribution:
                days_since_last = (datetime.utcnow() - stats.last_contribution).days
                if days_since_last <= 1:
                    stats.current_streak += 1
                    if stats.current_streak > stats.best_streak:
                        stats.best_streak = stats.current_streak
                else:
                    stats.current_streak = 1
            else:
                stats.current_streak = 1
                
        elif action == "approved":
            stats.approved_forms += 1
            stats.pending_forms = max(0, stats.pending_forms - 1)
            stats.last_approval = datetime.utcnow()
            
            if review_score:
                stats.update_average_score(review_score)
            
            # Check for tier upgrade
            stats.check_tier_upgrade()
            
        elif action == "rejected":
            stats.rejected_forms += 1
            stats.pending_forms = max(0, stats.pending_forms - 1)
            
        elif action == "revision":
            stats.revision_requests += 1
        
        # Calculate accuracy rate
        stats.calculate_accuracy_rate()
        
        self.db.commit()
    
    async def _process_approval_rewards(
        self,
        contributor_id: int,
        form_id: int,
        page_count: int
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Process rewards for approved form.
        Returns (reward_granted, reward_details).
        """
        stats = self.db.query(ContributorStats).filter(
            ContributorStats.contributor_id == contributor_id
        ).first()
        
        if not stats:
            return False, None
        
        # Update unique pages
        old_pages = stats.unique_pages_contributed
        stats.unique_pages_contributed += page_count
        stats.total_pages_submitted += page_count
        stats.unique_forms_contributed += 1
        
        # Calculate free weeks (10 pages = 1 week)
        old_weeks = old_pages // 10
        new_weeks = stats.unique_pages_contributed // 10
        weeks_to_grant = new_weeks - old_weeks
        
        if weeks_to_grant > 0:
            # Create reward ledger entry
            ledger_id = f"reward_{uuid.uuid4().hex[:12]}"
            
            reward = RewardLedger(
                ledger_id=ledger_id,
                contributor_id=contributor_id,
                form_id=form_id,
                reward_type="free_week",
                reward_amount=weeks_to_grant,
                reason=f"Reached {new_weeks * 10} unique pages milestone",
                milestone_type="10_pages",
                milestone_value=new_weeks * 10,
                expires_at=datetime.utcnow() + timedelta(days=365)  # 1 year expiry
            )
            
            self.db.add(reward)
            
            # Update stats
            stats.free_weeks_earned += weeks_to_grant
            stats.last_reward_granted = datetime.utcnow()
            
            # Check for bonus rewards
            bonus_rewards = []
            
            # First form approved
            if stats.approved_forms == 1:
                bonus = RewardLedger(
                    ledger_id=f"reward_{uuid.uuid4().hex[:12]}",
                    contributor_id=contributor_id,
                    form_id=form_id,
                    reward_type="free_week",
                    reward_amount=1,
                    reason="First form approved - Welcome bonus!",
                    milestone_type="first_approval",
                    milestone_value=1
                )
                self.db.add(bonus)
                stats.free_weeks_earned += 1
                bonus_rewards.append("First form bonus: 1 week")
            
            # Streak bonuses
            if stats.current_streak == 7:
                bonus = RewardLedger(
                    ledger_id=f"reward_{uuid.uuid4().hex[:12]}",
                    contributor_id=contributor_id,
                    form_id=form_id,
                    reward_type="free_week",
                    reward_amount=1,
                    reason="7-day contribution streak",
                    milestone_type="streak_bonus",
                    milestone_value=7
                )
                self.db.add(bonus)
                stats.free_weeks_earned += 1
                bonus_rewards.append("7-day streak bonus: 1 week")
            
            self.db.commit()
            
            reward_details = {
                "weeks_granted": weeks_to_grant,
                "total_pages": stats.unique_pages_contributed,
                "total_weeks_earned": stats.free_weeks_earned,
                "bonus_rewards": bonus_rewards
            }
            
            return True, reward_details
        
        return False, None
    
    def _field_to_dict(self, field: FormField) -> Dict[str, Any]:
        """Convert FormField object to dictionary."""
        return {
            "field_name": field.field_name,
            "field_label": field.field_label,
            "field_type": field.field_type,
            "field_order": field.field_order,
            "is_required": field.is_required,
            "is_repeatable": field.is_repeatable,
            "max_length": field.max_length,
            "min_length": field.min_length,
            "section_name": field.section_name,
            "group_name": field.group_name,
            "validation_rules": field.validation_rules,
            "default_value": field.default_value,
            "placeholder_text": field.placeholder_text,
            "help_text": field.help_text,
            "ai_field_category": field.ai_field_category
        }
    
    async def _get_related_forms(self, form: Form) -> List[Dict[str, Any]]:
        """Get forms related to the given form."""
        related = []
        
        # Same form number, different versions
        if form.form_number:
            version_matches = self.db.query(Form).filter(
                and_(
                    Form.form_number == form.form_number,
                    Form.id != form.id,
                    Form.status == FormStatus.APPROVED
                )
            ).limit(3).all()
            
            for match in version_matches:
                related.append({
                    "form_id": match.form_id,
                    "title": match.title,
                    "version": match.version,
                    "relation_type": "version"
                })
        
        # Same jurisdiction and type
        jurisdiction_matches = self.db.query(Form).filter(
            and_(
                Form.jurisdiction_id == form.jurisdiction_id,
                Form.form_type == form.form_type,
                Form.id != form.id,
                Form.status == FormStatus.APPROVED
            )
        ).limit(3).all()
        
        for match in jurisdiction_matches:
            if not any(r['form_id'] == match.form_id for r in related):
                related.append({
                    "form_id": match.form_id,
                    "title": match.title,
                    "relation_type": "similar"
                })
        
        return related[:5]  # Limit to 5 related forms
    
    async def _get_form_versions(self, form: Form) -> List[Dict[str, Any]]:
        """Get all versions of a form."""
        versions = self.db.query(FormVersion).filter(
            FormVersion.form_id == form.id
        ).order_by(desc(FormVersion.created_at)).all()
        
        return [
            {
                "version_number": v.version_number,
                "change_summary": v.change_summary,
                "change_type": v.change_type,
                "created_at": v.created_at.isoformat(),
                "changed_by": v.changed_by.email if v.changed_by else None
            }
            for v in versions
        ]
    
    def _calculate_next_milestone(
        self,
        stats: ContributorStats
    ) -> Optional[Dict[str, Any]]:
        """Calculate the next milestone for a contributor."""
        milestones = [
            {"pages": 10, "reward": "1 free week"},
            {"pages": 50, "reward": "5 free weeks + Silver tier"},
            {"pages": 100, "reward": "10 free weeks + Gold tier"},
            {"pages": 500, "reward": "50 free weeks + Platinum tier"},
            {"forms": 10, "reward": "Contributor badge"},
            {"forms": 50, "reward": "Expert contributor badge"},
            {"forms": 100, "reward": "Master contributor badge"}
        ]
        
        # Check page milestones
        for milestone in milestones:
            if "pages" in milestone and stats.unique_pages_contributed < milestone["pages"]:
                return {
                    "type": "pages",
                    "target": milestone["pages"],
                    "current": stats.unique_pages_contributed,
                    "progress": (stats.unique_pages_contributed / milestone["pages"]) * 100,
                    "reward": milestone["reward"]
                }
        
        # Check form milestones
        for milestone in milestones:
            if "forms" in milestone and stats.approved_forms < milestone["forms"]:
                return {
                    "type": "forms",
                    "target": milestone["forms"],
                    "current": stats.approved_forms,
                    "progress": (stats.approved_forms / milestone["forms"]) * 100,
                    "reward": milestone["reward"]
                }
        
        return None

























# services/forms/feedback_service.py
"""
Phase 12: Feedback Service
Handles user feedback submission, tracking, and resolution
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_

from models.forms import FormFeedback, Form, FormField, FeedbackStatus
from models.user import User
from schemas.forms import (
    FormFeedbackRequest, FormFeedbackResponse,
    FeedbackStatsResponse, FeedbackType, Priority
)
from services.notifications import NotificationService


class FeedbackService:
    """Service for managing user feedback and issue tracking."""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def submit_feedback(
        self,
        feedback_data: FormFeedbackRequest,
        user_id: int
    ) -> FormFeedbackResponse:
        """
        Submit structured user feedback for a form.
        Includes automatic prioritization and routing.
        """
        try:
            # Verify form exists
            form = self.db.query(Form).filter(
                Form.form_id == feedback_data.form_id
            ).first()
            
            if not form:
                raise ValueError("Form not found")
            
            # Generate IDs
            feedback_id = self._generate_feedback_id()
            ticket_number = self._generate_ticket_number()
            
            # Determine priority based on severity and type
            priority = self._calculate_priority(
                feedback_data.feedback_type,
                feedback_data.severity
            )
            
            # Create feedback record
            feedback = FormFeedback(
                feedback_id=feedback_id,
                form_id=form.id,
                user_id=user_id,
                feedback_type=feedback_data.feedback_type,
                feedback_category=self._categorize_feedback(feedback_data.feedback_type),
                title=feedback_data.title,
                content=feedback_data.content,
                severity=feedback_data.severity,
                field_name=feedback_data.field_name,
                suggested_correction=feedback_data.suggested_correction,
                contact_email=feedback_data.contact_email if feedback_data.allow_contact else None,
                ticket_number=ticket_number,
                status=FeedbackStatus.RECEIVED,
                priority=priority
            )
            
            # Find field if specified
            if feedback_data.field_name:
                field = self.db.query(FormField).filter(
                    and_(
                        FormField.form_id == form.id,
                        FormField.field_name == feedback_data.field_name
                    )
                ).first()
                
                if field:
                    feedback.field_id = field.id
            
            self.db.add(feedback)
            
            # Update form feedback count
            form.feedback_count += 1
            
            # Check if this is a widespread issue
            similar_feedback_count = await self._check_similar_feedback(
                form.id, feedback_data.feedback_type, feedback_data.field_name
            )
            
            if similar_feedback_count >= 3:
                feedback.priority = Priority.HIGH
                feedback.forms_affected = similar_feedback_count
                
                # Notify admins of trending issue
                await self.notification_service.notify_trending_issue(
                    form, feedback_data.feedback_type, similar_feedback_count
                )
            
            self.db.commit()
            self.db.refresh(feedback)
            
            # Auto-assign to admin if high priority
            if feedback.priority in [Priority.HIGH, Priority.URGENT]:
                await self._auto_assign_feedback(feedback)
            
            # Send confirmation notification
            await self.notification_service.notify_feedback_received(
                user_id, ticket_number
            )
            
            return FormFeedbackResponse(
                feedback_id=feedback_id,
                form_id=feedback_data.form_id,
                status=feedback.status,
                ticket_number=ticket_number,
                priority=feedback.priority,
                estimated_response_time=self._estimate_response_time(feedback.priority)
            )
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def update_feedback_status(
        self,
        feedback_id: str,
        status: FeedbackStatus,
        admin_id: int,
        admin_notes: Optional[str] = None,
        resolution_notes: Optional[str] = None,
        resolution_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update feedback status and resolution details."""
        feedback = self.db.query(FormFeedback).filter(
            FormFeedback.feedback_id == feedback_id
        ).first()
        
        if not feedback:
            raise ValueError("Feedback not found")
        
        # Update status
        old_status = feedback.status
        feedback.status = status
        feedback.admin_notes = admin_notes
        
        # Handle resolution
        if status in [FeedbackStatus.RESOLVED, FeedbackStatus.CLOSED, FeedbackStatus.WONT_FIX]:
            feedback.resolved_at = datetime.utcnow()
            feedback.resolved_by_id = admin_id
            feedback.resolution_notes = resolution_notes
            feedback.resolution_type = resolution_type
            
            # Update form if fix was deployed
            if resolution_type == "fixed":
                form = self.db.query(Form).filter(
                    Form.id == feedback.form_id
                ).first()
                
                if form:
                    form.last_verified_date = datetime.utcnow()
        
        # Assign to admin if not already assigned
        if not feedback.assigned_to_id:
            feedback.assigned_to_id = admin_id
        
        self.db.commit()
        
        # Send notification to user if they provided contact
        if feedback.contact_email and status != old_status:
            await self.notification_service.notify_feedback_updated(
                feedback.contact_email,
                feedback.ticket_number,
                status
            )
        
        return {
            "feedback_id": feedback_id,
            "status": status,
            "updated_at": datetime.utcnow(),
            "success": True,
            "message": "Feedback status updated"
        }
    
    async def vote_on_feedback(
        self,
        feedback_id: str,
        user_id: int,
        vote_type: str  # "up" or "down"
    ) -> Dict[str, Any]:
        """Allow users to vote on feedback relevance."""
        feedback = self.db.query(FormFeedback).filter(
            FormFeedback.feedback_id == feedback_id
        ).first()
        
        if not feedback:
            raise ValueError("Feedback not found")
        
        # Check if user already voted (would need a separate vote tracking table)
        # For now, just update counts
        
        if vote_type == "up":
            feedback.upvotes += 1
        elif vote_type == "down":
            feedback.downvotes += 1
        else:
            raise ValueError("Invalid vote type")
        
        # Recalculate impact score
        impact_score = feedback.calculate_impact_score()
        
        # Escalate if high impact
        if impact_score > 100 and feedback.priority == Priority.NORMAL:
            feedback.priority = Priority.HIGH
            await self._auto_assign_feedback(feedback)
        
        self.db.commit()
        
        return {
            "feedback_id": feedback_id,
            "upvotes": feedback.upvotes,
            "downvotes": feedback.downvotes,
            "impact_score": impact_score
        }
    
    async def get_form_feedback(
        self,
        form_id: str,
        status: Optional[FeedbackStatus] = None,
        feedback_type: Optional[FeedbackType] = None,
        sort_by: str = "created_at"
    ) -> List[Dict[str, Any]]:
        """Get all feedback for a specific form."""
        form = self.db.query(Form).filter(
            Form.form_id == form_id
        ).first()
        
        if not form:
            raise ValueError("Form not found")
        
        query = self.db.query(FormFeedback).filter(
            FormFeedback.form_id == form.id
        )
        
        if status:
            query = query.filter(FormFeedback.status == status)
            
        if feedback_type:
            query = query.filter(FormFeedback.feedback_type == feedback_type)
        
        # Apply sorting
        if sort_by == "severity":
            query = query.order_by(desc(FormFeedback.severity))
        elif sort_by == "votes":
            query = query.order_by(desc(FormFeedback.upvotes - FormFeedback.downvotes))
        else:
            query = query.order_by(desc(FormFeedback.created_at))
        
        feedback_list = query.all()
        
        return [
            self._feedback_to_dict(fb)
            for fb in feedback_list
        ]
    
    async def get_feedback_stats(
        self,
        time_period: Optional[int] = 30  # days
    ) -> FeedbackStatsResponse:
        """Get comprehensive feedback statistics."""
        # Date range
        start_date = datetime.utcnow() - timedelta(days=time_period)
        
        # Total counts
        total_feedback = self.db.query(FormFeedback).count()
        
        open_tickets = self.db.query(FormFeedback).filter(
            FormFeedback.status.in_([
                FeedbackStatus.RECEIVED,
                FeedbackStatus.TRIAGED,
                FeedbackStatus.IN_PROGRESS
            ])
        ).count()
        
        resolved_tickets = self.db.query(FormFeedback).filter(
            FormFeedback.status.in_([
                FeedbackStatus.RESOLVED,
                FeedbackStatus.CLOSED
            ])
        ).count()
        
        # Average resolution time
        resolved_feedback = self.db.query(FormFeedback).filter(
            and_(
                FormFeedback.resolved_at != None,
                FormFeedback.created_at != None,
                FormFeedback.created_at >= start_date
            )
        ).all()
        
        if resolved_feedback:
            total_resolution_time = sum(
                (fb.resolved_at - fb.created_at).total_seconds()
                for fb in resolved_feedback
            )
            avg_seconds = total_resolution_time / len(resolved_feedback)
            avg_hours = avg_seconds / 3600
            
            if avg_hours < 24:
                average_resolution_time = f"{avg_hours:.1f} hours"
            else:
                average_resolution_time = f"{avg_hours/24:.1f} days"
        else:
            average_resolution_time = None
        
        # Breakdown by type
        feedback_by_type = {}
        type_counts = self.db.query(
            FormFeedback.feedback_type,
            func.count(FormFeedback.id)
        ).group_by(FormFeedback.feedback_type).all()
        
        for fb_type, count in type_counts:
            feedback_by_type[fb_type] = count
        
        # Breakdown by severity
        feedback_by_severity = {}
        severity_counts = self.db.query(
            FormFeedback.severity,
            func.count(FormFeedback.id)
        ).group_by(FormFeedback.severity).all()
        
        for severity, count in severity_counts:
            feedback_by_severity[str(severity)] = count
        
        # Breakdown by status
        feedback_by_status = {}
        status_counts = self.db.query(
            FormFeedback.status,
            func.count(FormFeedback.id)
        ).group_by(FormFeedback.status).all()
        
        for status, count in status_counts:
            feedback_by_status[status] = count
        
        # User satisfaction (based on resolution and votes)
        satisfaction_data = self.db.query(
            func.sum(FormFeedback.upvotes),
            func.sum(FormFeedback.downvotes)
        ).filter(
            FormFeedback.status == FeedbackStatus.RESOLVED
        ).first()
        
        if satisfaction_data[0] and satisfaction_data[1]:
            total_votes = satisfaction_data[0] + satisfaction_data[1]
            user_satisfaction = (satisfaction_data[0] / total_votes) * 5.0
        else:
            user_satisfaction = None
        
        # Resolution rate
        if total_feedback > 0:
            resolution_rate = (resolved_tickets / total_feedback) * 100
        else:
            resolution_rate = None
        
        # Recent activity
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        
        feedback_today = self.db.query(FormFeedback).filter(
            func.date(FormFeedback.created_at) == today
        ).count()
        
        feedback_this_week = self.db.query(FormFeedback).filter(
            FormFeedback.created_at >= week_ago
        ).count()
        
        # Trending issues (most reported in last 7 days)
        trending_query = self.db.query(
            FormFeedback.feedback_type,
            FormFeedback.feedback_category,
            func.count(FormFeedback.id).label('count')
        ).filter(
            FormFeedback.created_at >= week_ago
        ).group_by(
            FormFeedback.feedback_type,
            FormFeedback.feedback_category
        ).order_by(
            desc('count')
        ).limit(5).all()
        
        trending_issues = [
            {
                "type": issue[0],
                "category": issue[1],
                "count": issue[2]
            }
            for issue in trending_query
        ]
        
        # Most reported forms
        most_reported_query = self.db.query(
            Form.form_id,
            Form.title,
            func.count(FormFeedback.id).label('feedback_count')
        ).join(
            FormFeedback, Form.id == FormFeedback.form_id
        ).group_by(
            Form.id, Form.form_id, Form.title
        ).order_by(
            desc('feedback_count')
        ).limit(5).all()
        
        most_reported_forms = [
            {
                "form_id": form[0],
                "title": form[1],
                "feedback_count": form[2]
            }
            for form in most_reported_query
        ]
        
        # Most common issues
        common_issues_query = self.db.query(
            FormFeedback.title,
            FormFeedback.feedback_type,
            func.count(FormFeedback.id).label('occurrence_count')
        ).filter(
            FormFeedback.title != None
        ).group_by(
            FormFeedback.title,
            FormFeedback.feedback_type
        ).order_by(
            desc('occurrence_count')
        ).limit(5).all()
        
        most_common_issues = [
            {
                "title": issue[0],
                "type": issue[1],
                "occurrence_count": issue[2]
            }
            for issue in common_issues_query
        ]
        
        return FeedbackStatsResponse(
            total_feedback=total_feedback,
            open_tickets=open_tickets,
            resolved_tickets=resolved_tickets,
            average_resolution_time=average_resolution_time,
            feedback_by_type=feedback_by_type,
            feedback_by_severity=feedback_by_severity,
            feedback_by_status=feedback_by_status,
            user_satisfaction=user_satisfaction,
            resolution_rate=resolution_rate,
            feedback_today=feedback_today,
            feedback_this_week=feedback_this_week,
            trending_issues=trending_issues,
            most_reported_forms=most_reported_forms,
            most_common_issues=most_common_issues
        )
    
    async def get_my_feedback(
        self,
        user_id: int,
        include_resolved: bool = True
    ) -> List[Dict[str, Any]]:
        """Get feedback submitted by a specific user."""
        query = self.db.query(FormFeedback).options(
            joinedload(FormFeedback.form)
        ).filter(
            FormFeedback.user_id == user_id
        )
        
        if not include_resolved:
            query = query.filter(
                ~FormFeedback.status.in_([
                    FeedbackStatus.RESOLVED,
                    FeedbackStatus.CLOSED,
                    FeedbackStatus.WONT_FIX
                ])
            )
        
        feedback_list = query.order_by(
            desc(FormFeedback.created_at)
        ).all()
        
        return [
            {
                **self._feedback_to_dict(fb),
                "form_title": fb.form.title if fb.form else None
            }
            for fb in feedback_list
        ]
    
    async def bulk_update_feedback(
        self,
        feedback_ids: List[str],
        status: Optional[FeedbackStatus] = None,
        assigned_to_id: Optional[int] = None,
        priority: Optional[Priority] = None
    ) -> Dict[str, Any]:
        """Bulk update multiple feedback items."""
        updated_count = 0
        
        for feedback_id in feedback_ids:
            feedback = self.db.query(FormFeedback).filter(
                FormFeedback.feedback_id == feedback_id
            ).first()
            
            if feedback:
                if status:
                    feedback.status = status
                if assigned_to_id:
                    feedback.assigned_to_id = assigned_to_id
                if priority:
                    feedback.priority = priority
                    
                updated_count += 1
        
        self.db.commit()
        
        return {
            "updated_count": updated_count,
            "total_requested": len(feedback_ids),
            "success": True
        }
    
    # Private helper methods
    
    def _generate_feedback_id(self) -> str:
        """Generate unique feedback ID."""
        return f"fb_{uuid.uuid4().hex[:8]}"
    
    def _generate_ticket_number(self) -> str:
        """Generate human-readable ticket number."""
        # Get today's count
        today = datetime.utcnow().date()
        today_count = self.db.query(FormFeedback).filter(
            func.date(FormFeedback.created_at) == today
        ).count()
        
        # Format: GLD-YYYYMMDD-XXXX
        return f"GLD-{today.strftime('%Y%m%d')}-{today_count + 1:04d}"
    
    def _calculate_priority(
        self,
        feedback_type: FeedbackType,
        severity: int
    ) -> Priority:
        """Calculate priority based on type and severity."""
        # Critical types always get higher priority
        critical_types = [
            FeedbackType.FIELD_ERROR,
            FeedbackType.CONTENT_ISSUE,
            FeedbackType.JURISDICTION_WRONG,
            FeedbackType.OUTDATED_FORM
        ]
        
        if feedback_type in critical_types:
            if severity >= 4:
                return Priority.URGENT
            elif severity >= 3:
                return Priority.HIGH
            else:
                return Priority.NORMAL
        else:
            if severity >= 5:
                return Priority.HIGH
            elif severity >= 3:
                return Priority.NORMAL
            else:
                return Priority.LOW
    
    def _categorize_feedback(self, feedback_type: FeedbackType) -> str:
        """Categorize feedback type into broader categories."""
        category_map = {
            FeedbackType.FIELD_ERROR: "content",
            FeedbackType.PARSING_ISSUE: "technical",
            FeedbackType.JURISDICTION_WRONG: "content",
            FeedbackType.CONTENT_ISSUE: "content",
            FeedbackType.MISSING_FIELD: "content",
            FeedbackType.INCORRECT_FORMAT: "formatting",
            FeedbackType.OUTDATED_FORM: "content",
            FeedbackType.TRANSLATION_ERROR: "content",
            FeedbackType.INSTRUCTION_UNCLEAR: "instructions",
            FeedbackType.TECHNICAL_ISSUE: "technical",
            FeedbackType.SUGGESTION: "enhancement",
            FeedbackType.COMPLAINT: "general",
            FeedbackType.PRAISE: "general"
        }
        
        return category_map.get(feedback_type, "general")
    
    def _estimate_response_time(self, priority: Priority) -> str:
        """Estimate response time based on priority."""
        estimates = {
            Priority.URGENT: "2-4 hours",
            Priority.HIGH: "1 business day",
            Priority.NORMAL: "2-3 business days",
            Priority.LOW: "5-7 business days"
        }
        
        return estimates.get(priority, "2-3 business days")
    
    async def _check_similar_feedback(
        self,
        form_id: int,
        feedback_type: FeedbackType,
        field_name: Optional[str] = None
    ) -> int:
        """Check for similar feedback on the same form."""
        query = self.db.query(FormFeedback).filter(
            and_(
                FormFeedback.form_id == form_id,
                FormFeedback.feedback_type == feedback_type
            )
        )
        
        if field_name:
            query = query.filter(FormFeedback.field_name == field_name)
        
        return query.count()
    
    async def _auto_assign_feedback(self, feedback: FormFeedback):
        """Auto-assign high priority feedback to available admin."""
        # Find admin with least assigned feedback
        admin_query = self.db.query(
            User.id,
            func.count(FormFeedback.id).label('assigned_count')
        ).outerjoin(
            FormFeedback,
            and_(
                FormFeedback.assigned_to_id == User.id,
                FormFeedback.status.in_([
                    FeedbackStatus.TRIAGED,
                    FeedbackStatus.IN_PROGRESS
                ])
            )
        ).filter(
            User.is_admin == True,
            User.is_active == True
        ).group_by(User.id).order_by('assigned_count').first()
        
        if admin_query:
            feedback.assigned_to_id = admin_query[0]
            feedback.status = FeedbackStatus.TRIAGED
            
            # Send notification to assigned admin
            await self.notification_service.notify_feedback_assigned(
                admin_query[0],
                feedback.ticket_number,
                feedback.priority
            )
    
    def _feedback_to_dict(self, feedback: FormFeedback) -> Dict[str, Any]:
        """Convert feedback object to dictionary."""
        return {
            "feedback_id": feedback.feedback_id,
            "form_id": feedback.form.form_id if feedback.form else None,
            "feedback_type": feedback.feedback_type,
            "feedback_category": feedback.feedback_category,
            "title": feedback.title,
            "content": feedback.content,
            "severity": feedback.severity,
            "field_name": feedback.field_name,
            "suggested_correction": feedback.suggested_correction,
            "ticket_number": feedback.ticket_number,
            "status": feedback.status,
            "priority": feedback.priority,
            "upvotes": feedback.upvotes,
            "downvotes": feedback.downvotes,
            "impact_score": feedback.calculate_impact_score(),
            "created_at": feedback.created_at.isoformat(),
            "resolved_at": feedback.resolved_at.isoformat() if feedback.resolved_at else None,
            "assigned_to": feedback.assigned_to.email if feedback.assigned_to else None
        }





































# services/forms/feedback_service.py
"""
Phase 12: Feedback Service
Handles user feedback submission, tracking, and resolution
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_

from models.forms import FormFeedback, Form, FormField, FeedbackStatus
from models.user import User
from schemas.forms import (
    FormFeedbackRequest, FormFeedbackResponse,
    FeedbackStatsResponse, FeedbackType, Priority
)
from services.notifications import NotificationService


class FeedbackService:
    """Service for managing user feedback and issue tracking."""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def submit_feedback(
        self,
        feedback_data: FormFeedbackRequest,
        user_id: int
    ) -> FormFeedbackResponse:
        """
        Submit structured user feedback for a form.
        Includes automatic prioritization and routing.
        """
        try:
            # Verify form exists
            form = self.db.query(Form).filter(
                Form.form_id == feedback_data.form_id
            ).first()
            
            if not form:
                raise ValueError("Form not found")
            
            # Generate IDs
            feedback_id = self._generate_feedback_id()
            ticket_number = self._generate_ticket_number()
            
            # Determine priority based on severity and type
            priority = self._calculate_priority(
                feedback_data.feedback_type,
                feedback_data.severity
            )
            
            # Create feedback record
            feedback = FormFeedback(
                feedback_id=feedback_id,
                form_id=form.id,
                user_id=user_id,
                feedback_type=feedback_data.feedback_type,
                feedback_category=self._categorize_feedback(feedback_data.feedback_type),
                title=feedback_data.title,
                content=feedback_data.content,
                severity=feedback_data.severity,
                field_name=feedback_data.field_name,
                suggested_correction=feedback_data.suggested_correction,
                contact_email=feedback_data.contact_email if feedback_data.allow_contact else None,
                ticket_number=ticket_number,
                status=FeedbackStatus.RECEIVED,
                priority=priority
            )
            
            # Find field if specified
            if feedback_data.field_name:
                field = self.db.query(FormField).filter(
                    and_(
                        FormField.form_id == form.id,
                        FormField.field_name == feedback_data.field_name
                    )
                ).first()
                
                if field:
                    feedback.field_id = field.id
            
            self.db.add(feedback)
            
            # Update form feedback count
            form.feedback_count += 1
            
            # Check if this is a widespread issue
            similar_feedback_count = await self._check_similar_feedback(
                form.id, feedback_data.feedback_type, feedback_data.field_name
            )
            
            if similar_feedback_count >= 3:
                feedback.priority = Priority.HIGH
                feedback.forms_affected = similar_feedback_count
                
                # Notify admins of trending issue
                await self.notification_service.notify_trending_issue(
                    form, feedback_data.feedback_type, similar_feedback_count
                )
            
            self.db.commit()
            self.db.refresh(feedback)
            
            # Auto-assign to admin if high priority
            if feedback.priority in [Priority.HIGH, Priority.URGENT]:
                await self._auto_assign_feedback(feedback)
            
            # Send confirmation notification
            await self.notification_service.notify_feedback_received(
                user_id, ticket_number
            )
            
            return FormFeedbackResponse(
                feedback_id=feedback_id,
                form_id=feedback_data.form_id,
                status=feedback.status,
                ticket_number=ticket_number,
                priority=feedback.priority,
                estimated_response_time=self._estimate_response_time(feedback.priority)
            )
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def update_feedback_status(
        self,
        feedback_id: str,
        status: FeedbackStatus,
        admin_id: int,
        admin_notes: Optional[str] = None,
        resolution_notes: Optional[str] = None,
        resolution_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update feedback status and resolution details."""
        feedback = self.db.query(FormFeedback).filter(
            FormFeedback.feedback_id == feedback_id
        ).first()
        
        if not feedback:
            raise ValueError("Feedback not found")
        
        # Update status
        old_status = feedback.status
        feedback.status = status
        feedback.admin_notes = admin_notes
        
        # Handle resolution
        if status in [FeedbackStatus.RESOLVED, FeedbackStatus.CLOSED, FeedbackStatus.WONT_FIX]:
            feedback.resolved_at = datetime.utcnow()
            feedback.resolved_by_id = admin_id
            feedback.resolution_notes = resolution_notes
            feedback.resolution_type = resolution_type
            
            # Update form if fix was deployed
            if resolution_type == "fixed":
                form = self.db.query(Form).filter(
                    Form.id == feedback.form_id
                ).first()
                
                if form:
                    form.last_verified_date = datetime.utcnow()
        
        # Assign to admin if not already assigned
        if not feedback.assigned_to_id:
            feedback.assigned_to_id = admin_id
        
        self.db.commit()
        
        # Send notification to user if they provided contact
        if feedback.contact_email and status != old_status:
            await self.notification_service.notify_feedback_updated(
                feedback.contact_email,
                feedback.ticket_number,
                status
            )
        
        return {
            "feedback_id": feedback_id,
            "status": status,
            "updated_at": datetime.utcnow(),
            "success": True,
            "message": "Feedback status updated"
        }
    
    async def vote_on_feedback(
        self,
        feedback_id: str,
        user_id: int,
        vote_type: str  # "up" or "down"
    ) -> Dict[str, Any]:
        """Allow users to vote on feedback relevance."""
        feedback = self.db.query(FormFeedback).filter(
            FormFeedback.feedback_id == feedback_id
        ).first()
        
        if not feedback:
            raise ValueError("Feedback not found")
        
        # Check if user already voted (would need a separate vote tracking table)
        # For now, just update counts
        
        if vote_type == "up":
            feedback.upvotes += 1
        elif vote_type == "down":
            feedback.downvotes += 1
        else:
            raise ValueError("Invalid vote type")
        
        # Recalculate impact score
        impact_score = feedback.calculate_impact_score()
        
        # Escalate if high impact
        if impact_score > 100 and feedback.priority == Priority.NORMAL:
            feedback.priority = Priority.HIGH
            await self._auto_assign_feedback(feedback)
        
        self.db.commit()
        
        return {
            "feedback_id": feedback_id,
            "upvotes": feedback.upvotes,
            "downvotes": feedback.downvotes,
            "impact_score": impact_score
        }
    
    async def get_form_feedback(
        self,
        form_id: str,
        status: Optional[FeedbackStatus] = None,
        feedback_type: Optional[FeedbackType] = None,
        sort_by: str = "created_at"
    ) -> List[Dict[str, Any]]:
        """Get all feedback for a specific form."""
        form = self.db.query(Form).filter(
            Form.form_id == form_id
        ).first()
        
        if not form:
            raise ValueError("Form not found")
        
        query = self.db.query(FormFeedback).filter(
            FormFeedback.form_id == form.id
        )
        
        if status:
            query = query.filter(FormFeedback.status == status)
            
        if feedback_type:
            query = query.filter(FormFeedback.feedback_type == feedback_type)
        
        # Apply sorting
        if sort_by == "severity":
            query = query.order_by(desc(FormFeedback.severity))
        elif sort_by == "votes":
            query = query.order_by(desc(FormFeedback.upvotes - FormFeedback.downvotes))
        else:
            query = query.order_by(desc(FormFeedback.created_at))
        
        feedback_list = query.all()
        
        return [
            self._feedback_to_dict(fb)
            for fb in feedback_list
        ]
    
    async def get_feedback_stats(
        self,
        time_period: Optional[int] = 30  # days
    ) -> FeedbackStatsResponse:
        """Get comprehensive feedback statistics."""
        # Date range
        start_date = datetime.utcnow() - timedelta(days=time_period)
        
        # Total counts
        total_feedback = self.db.query(FormFeedback).count()
        
        open_tickets = self.db.query(FormFeedback).filter(
            FormFeedback.status.in_([
                FeedbackStatus.RECEIVED,
                FeedbackStatus.TRIAGED,
                FeedbackStatus.IN_PROGRESS
            ])
        ).count()
        
        resolved_tickets = self.db.query(FormFeedback).filter(
            FormFeedback.status.in_([
                FeedbackStatus.RESOLVED,
                FeedbackStatus.CLOSED
            ])
        ).count()
        
        # Average resolution time
        resolved_feedback = self.db.query(FormFeedback).filter(
            and_(
                FormFeedback.resolved_at != None,
                FormFeedback.created_at != None,
                FormFeedback.created_at >= start_date
            )
        ).all()
        
        if resolved_feedback:
            total_resolution_time = sum(
                (fb.resolved_at - fb.created_at).total_seconds()
                for fb in resolved_feedback
            )
            avg_seconds = total_resolution_time / len(resolved_feedback)
            avg_hours = avg_seconds / 3600
            
            if avg_hours < 24:
                average_resolution_time = f"{avg_hours:.1f} hours"
            else:
                average_resolution_time = f"{avg_hours/24:.1f} days"
        else:
            average_resolution_time = None
        
        # Breakdown by type
        feedback_by_type = {}
        type_counts = self.db.query(
            FormFeedback.feedback_type,
            func.count(FormFeedback.id)
        ).group_by(FormFeedback.feedback_type).all()
        
        for fb_type, count in type_counts:
            feedback_by_type[fb_type] = count
        
        # Breakdown by severity
        feedback_by_severity = {}
        severity_counts = self.db.query(
            FormFeedback.severity,
            func.count(FormFeedback.id)
        ).group_by(FormFeedback.severity).all()
        
        for severity, count in severity_counts:
            feedback_by_severity[str(severity)] = count
        
        # Breakdown by status
        feedback_by_status = {}
        status_counts = self.db.query(
            FormFeedback.status,
            func.count(FormFeedback.id)
        ).group_by(FormFeedback.status).all()
        
        for status, count in status_counts:
            feedback_by_status[status] = count
        
        # User satisfaction (based on resolution and votes)
        satisfaction_data = self.db.query(
            func.sum(FormFeedback.upvotes),
            func.sum(FormFeedback.downvotes)
        ).filter(
            FormFeedback.status == FeedbackStatus.RESOLVED
        ).first()
        
        if satisfaction_data[0] and satisfaction_data[1]:
            total_votes = satisfaction_data[0] + satisfaction_data[1]
            user_satisfaction = (satisfaction_data[0] / total_votes) * 5.0
        else:
            user_satisfaction = None
        
        # Resolution rate
        if total_feedback > 0:
            resolution_rate = (resolved_tickets / total_feedback) * 100
        else:
            resolution_rate = None
        
        # Recent activity
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        
        feedback_today = self.db.query(FormFeedback).filter(
            func.date(FormFeedback.created_at) == today
        ).count()
        
        feedback_this_week = self.db.query(FormFeedback).filter(
            FormFeedback.created_at >= week_ago
        ).count()
        
        # Trending issues (most reported in last 7 days)
        trending_query = self.db.query(
            FormFeedback.feedback_type,
            FormFeedback.feedback_category,
            func.count(FormFeedback.id).label('count')
        ).filter(
            FormFeedback.created_at >= week_ago
        ).group_by(
            FormFeedback.feedback_type,
            FormFeedback.feedback_category
        ).order_by(
            desc('count')
        ).limit(5).all()
        
        trending_issues = [
            {
                "type": issue[0],
                "category": issue[1],
                "count": issue[2]
            }
            for issue in trending_query
        ]
        
        # Most reported forms
        most_reported_query = self.db.query(
            Form.form_id,
            Form.title,
            func.count(FormFeedback.id).label('feedback_count')
        ).join(
            FormFeedback, Form.id == FormFeedback.form_id
        ).group_by(
            Form.id, Form.form_id, Form.title
        ).order_by(
            desc('feedback_count')
        ).limit(5).all()
        
        most_reported_forms = [
            {
                "form_id": form[0],
                "title": form[1],
                "feedback_count": form[2]
            }
            for form in most_reported_query
        ]
        
        # Most common issues
        common_issues_query = self.db.query(
            FormFeedback.title,
            FormFeedback.feedback_type,
            func.count(FormFeedback.id).label('occurrence_count')
        ).filter(
            FormFeedback.title != None
        ).group_by(
            FormFeedback.title,
            FormFeedback.feedback_type
        ).order_by(
            desc('occurrence_count')
        ).limit(5).all()
        
        most_common_issues = [
            {
                "title": issue[0],
                "type": issue[1],
                "occurrence_count": issue[2]
            }
            for issue in common_issues_query
        ]
        
        return FeedbackStatsResponse(
            total_feedback=total_feedback,
            open_tickets=open_tickets,
            resolved_tickets=resolved_tickets,
            average_resolution_time=average_resolution_time,
            feedback_by_type=feedback_by_type,
            feedback_by_severity=feedback_by_severity,
            feedback_by_status=feedback_by_status,
            user_satisfaction=user_satisfaction,
            resolution_rate=resolution_rate,
            feedback_today=feedback_today,
            feedback_this_week=feedback_this_week,
            trending_issues=trending_issues,
            most_reported_forms=most_reported_forms,
            most_common_issues=most_common_issues
        )
    
    async def get_my_feedback(
        self,
        user_id: int,
        include_resolved: bool = True
    ) -> List[Dict[str, Any]]:
        """Get feedback submitted by a specific user."""
        query = self.db.query(FormFeedback).options(
            joinedload(FormFeedback.form)
        ).filter(
            FormFeedback.user_id == user_id
        )
        
        if not include_resolved:
            query = query.filter(
                ~FormFeedback.status.in_([
                    FeedbackStatus.RESOLVED,
                    FeedbackStatus.CLOSED,
                    FeedbackStatus.WONT_FIX
                ])
            )
        
        feedback_list = query.order_by(
            desc(FormFeedback.created_at)
        ).all()
        
        return [
            {
                **self._feedback_to_dict(fb),
                "form_title": fb.form.title if fb.form else None
            }
            for fb in feedback_list
        ]
    
    async def bulk_update_feedback(
        self,
        feedback_ids: List[str],
        status: Optional[FeedbackStatus] = None,
        assigned_to_id: Optional[int] = None,
        priority: Optional[Priority] = None
    ) -> Dict[str, Any]:
        """Bulk update multiple feedback items."""
        updated_count = 0
        
        for feedback_id in feedback_ids:
            feedback = self.db.query(FormFeedback).filter(
                FormFeedback.feedback_id == feedback_id
            ).first()
            
            if feedback:
                if status:
                    feedback.status = status
                if assigned_to_id:
                    feedback.assigned_to_id = assigned_to_id
                if priority:
                    feedback.priority = priority
                    
                updated_count += 1
        
        self.db.commit()
        
        return {
            "updated_count": updated_count,
            "total_requested": len(feedback_ids),
            "success": True
        }
    
    # Private helper methods
    
    def _generate_feedback_id(self) -> str:
        """Generate unique feedback ID."""
        return f"fb_{uuid.uuid4().hex[:8]}"
    
    def _generate_ticket_number(self) -> str:
        """Generate human-readable ticket number."""
        # Get today's count
        today = datetime.utcnow().date()
        today_count = self.db.query(FormFeedback).filter(
            func.date(FormFeedback.created_at) == today
        ).count()
        
        # Format: GLD-YYYYMMDD-XXXX
        return f"GLD-{today.strftime('%Y%m%d')}-{today_count + 1:04d}"
    
    def _calculate_priority(
        self,
        feedback_type: FeedbackType,
        severity: int
    ) -> Priority:
        """Calculate priority based on type and severity."""
        # Critical types always get higher priority
        critical_types = [
            FeedbackType.FIELD_ERROR,
            FeedbackType.CONTENT_ISSUE,
            FeedbackType.JURISDICTION_WRONG,
            FeedbackType.OUTDATED_FORM
        ]
        
        if feedback_type in critical_types:
            if severity >= 4:
                return Priority.URGENT
            elif severity >= 3:
                return Priority.HIGH
            else:
                return Priority.NORMAL
        else:
            if severity >= 5:
                return Priority.HIGH
            elif severity >= 3:
                return Priority.NORMAL
            else:
                return Priority.LOW
    
    def _categorize_feedback(self, feedback_type: FeedbackType) -> str:
        """Categorize feedback type into broader categories."""
        category_map = {
            FeedbackType.FIELD_ERROR: "content",
            FeedbackType.PARSING_ISSUE: "technical",
            FeedbackType.JURISDICTION_WRONG: "content",
            FeedbackType.CONTENT_ISSUE: "content",
            FeedbackType.MISSING_FIELD: "content",
            FeedbackType.INCORRECT_FORMAT: "formatting",
            FeedbackType.OUTDATED_FORM: "content",
            FeedbackType.TRANSLATION_ERROR: "content",
            FeedbackType.INSTRUCTION_UNCLEAR: "instructions",
            FeedbackType.TECHNICAL_ISSUE: "technical",
            FeedbackType.SUGGESTION: "enhancement",
            FeedbackType.COMPLAINT: "general",
            FeedbackType.PRAISE: "general"
        }
        
        return category_map.get(feedback_type, "general")
    
    def _estimate_response_time(self, priority: Priority) -> str:
        """Estimate response time based on priority."""
        estimates = {
            Priority.URGENT: "2-4 hours",
            Priority.HIGH: "1 business day",
            Priority.NORMAL: "2-3 business days",
            Priority.LOW: "5-7 business days"
        }
        
        return estimates.get(priority, "2-3 business days")
    
    async def _check_similar_feedback(
        self,
        form_id: int,
        feedback_type: FeedbackType,
        field_name: Optional[str] = None
    ) -> int:
        """Check for similar feedback on the same form."""
        query = self.db.query(FormFeedback).filter(
            and_(
                FormFeedback.form_id == form_id,
                FormFeedback.feedback_type == feedback_type
            )
        )
        
        if field_name:
            query = query.filter(FormFeedback.field_name == field_name)
        
        return query.count()
    
    async def _auto_assign_feedback(self, feedback: FormFeedback):
        """Auto-assign high priority feedback to available admin."""
        # Find admin with least assigned feedback
        admin_query = self.db.query(
            User.id,
            func.count(FormFeedback.id).label('assigned_count')
        ).outerjoin(
            FormFeedback,
            and_(
                FormFeedback.assigned_to_id == User.id,
                FormFeedback.status.in_([
                    FeedbackStatus.TRIAGED,
                    FeedbackStatus.IN_PROGRESS
                ])
            )
        ).filter(
            User.is_admin == True,
            User.is_active == True
        ).group_by(User.id).order_by('assigned_count').first()
        
        if admin_query:
            feedback.assigned_to_id = admin_query[0]
            feedback.status = FeedbackStatus.TRIAGED
            
            # Send notification to assigned admin
            await self.notification_service.notify_feedback_assigned(
                admin_query[0],
                feedback.ticket_number,
                feedback.priority
            )
    
    def _feedback_to_dict(self, feedback: FormFeedback) -> Dict[str, Any]:
        """Convert feedback object to dictionary."""
        return {
            "feedback_id": feedback.feedback_id,
            "form_id": feedback.form.form_id if feedback.form else None,
            "feedback_type": feedback.feedback_type,
            "feedback_category": feedback.feedback_category,
            "title": feedback.title,
            "content": feedback.content,
            "severity": feedback.severity,
            "field_name": feedback.field_name,
            "suggested_correction": feedback.suggested_correction,
            "ticket_number": feedback.ticket_number,
            "status": feedback.status,
            "priority": feedback.priority,
            "upvotes": feedback.upvotes,
            "downvotes": feedback.downvotes,
            "impact_score": feedback.calculate_impact_score(),
            "created_at": feedback.created_at.isoformat(),
            "resolved_at": feedback.resolved_at.isoformat() if feedback.resolved_at else None,
            "assigned_to": feedback.assigned_to.email if feedback.assigned_to else None
        }


































# main.py
"""
Phase 12: Goldleaves Main Application
Integrates all services including form crowdsourcing
"""

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import sys

# Import database and models
from core.db.base import Base
from core.db.session import engine

# Import routers
from routers.auth import router as auth_router
from routers.api.v2.frontend_sync import router as frontend_router
from routers.api.v2.forms import router as forms_router
from routers.websocket import router as websocket_router

# Import middleware
from middleware.rate_limit import RateLimitMiddleware
from middleware.logging import LoggingMiddleware

# Import configuration
from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('goldleaves.log')
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Goldleaves Backend starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")
    
    # Create database tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    
    # Initialize services
    logger.info("Initializing services...")
    # TODO: Initialize background tasks, caches, etc.
    
    logger.info("✅ Goldleaves Backend ready to serve requests")
    
    yield
    
    # Shutdown
    logger.info("🛑 Goldleaves Backend shutting down...")
    # TODO: Cleanup tasks, close connections, etc.
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Create FastAPI app
    app = FastAPI(
        title="Goldleaves Legal Platform API",
        description="""
        Goldleaves is an AI-powered legal automation platform designed to serve:
        - Pro se litigants needing accessible legal help
        - Legal aid clinics with limited resources  
        - Solo practitioners seeking efficiency
        
        Phase 12 Features:
        - Legal form crowdsourcing and registry
        - Paralegal data acquisition support
        - Contributor reward system (10 pages = 1 week free)
        - Comprehensive feedback and quality control
        """,
        version="1.12.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None
    )
    
    # Add middleware
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"]
    )
    
    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Trusted host (production only)
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.goldleaves.com", "goldleaves.com"]
        )
    
    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        calls=100,
        period=60,
        scope="ip"
    )
    
    # Request logging
    app.add_middleware(LoggingMiddleware)
    
    # Include routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(frontend_router, prefix="/api")
    app.include_router(forms_router, prefix="/api")
    app.include_router(websocket_router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Goldleaves API",
            "version": "1.12.0",
            "phase": "12 - Form Crowdsourcing",
            "status": "operational",
            "documentation": "/api/docs",
            "health": "/health",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Comprehensive health check."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.12.0",
            "services": {
                "database": "healthy",  # TODO: Actual DB check
                "storage": "healthy",   # TODO: Storage check
                "cache": "healthy",     # TODO: Cache check
                "websocket": "healthy"  # TODO: WS check
            },
            "features": {
                "authentication": "enabled",
                "forms": "enabled",
                "feedback": "enabled",
                "rewards": "enabled",
                "websocket": "enabled"
            }
        }
        
        # Check if any service is unhealthy
        if any(status != "healthy" for status in health_status["services"].values()):
            health_status["status"] = "degraded"
            
        return health_status
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for unhandled errors."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        # Don't expose internal errors in production
        if settings.ENVIRONMENT == "production":
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Internal server error",
                    "message": str(exc),
                    "type": type(exc).__name__,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    # Custom 404 handler
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        """Custom 404 handler."""
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "Not found",
                "message": f"The requested resource '{request.url.path}' was not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    # API metrics endpoint (admin only)
    @app.get("/api/metrics")
    async def api_metrics():
        """Get API usage metrics (requires admin auth)."""
        # TODO: Implement with proper auth
        return {
            "total_requests": 0,
            "total_users": 0,
            "total_forms": 0,
            "active_sessions": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level="info",
        access_log=True,
        workers=1 if settings.ENVIRONMENT == "development" else 4
    )































    




