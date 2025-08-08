"""
Phase 12: Form Models for Crowdsourcing System
Complete database models for forms, contributors, and rewards
"""

from __future__ import annotations
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float, Enum, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, List, Any, Optional

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
