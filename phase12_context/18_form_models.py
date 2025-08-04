# models/form.py
"""
Form models for Phase 12 crowdsourcing system.
Defines database models for forms, contributors, and rewards.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from .dependencies import Base, TimestampMixin, SoftDeleteMixin


class FormType(PyEnum):
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


class FormStatus(PyEnum):
    """Status of form in review process."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ContributorType(PyEnum):
    """Types of contributors."""
    PARALEGAL = "paralegal"
    CROWDSOURCE = "crowdsource"
    MANUAL = "manual"
    ADMIN = "admin"


class Form(Base, TimestampMixin, SoftDeleteMixin):
    """Model for uploaded forms."""
    __tablename__ = "forms"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(String(32), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    form_type = Column(Enum(FormType), nullable=False, index=True)
    status = Column(Enum(FormStatus), default=FormStatus.PENDING, index=True)
    contributor_type = Column(Enum(ContributorType), default=ContributorType.CROWDSOURCE)
    
    # Relationships
    contributor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    contributor = relationship("User", foreign_keys=[contributor_id], back_populates="contributed_forms")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    organization = relationship("Organization")
    
    # Form content and metadata
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)
    content_type = Column(String(100), nullable=True)
    page_count = Column(Integer, nullable=True)
    
    # Review information
    reviewed_at = Column(DateTime, nullable=True)
    review_comments = Column(Text, nullable=True)
    review_score = Column(Float, nullable=True)
    
    # Metadata and tags
    metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Usage statistics
    download_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=False)
    
    # Composite indexes
    __table_args__ = (
        Index('idx_form_type_status', 'form_type', 'status'),
        Index('idx_contributor_status', 'contributor_id', 'status'),
        Index('idx_created_status', 'created_at', 'status'),
    )
    
    def __repr__(self):
        return f"<Form(id={self.id}, title='{self.title}', status={self.status.value})>"


class ContributorStats(Base, TimestampMixin):
    """Model for tracking contributor statistics and rewards."""
    __tablename__ = "contributor_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    contributor_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Contribution statistics
    total_forms_submitted = Column(Integer, default=0)
    approved_forms = Column(Integer, default=0)
    rejected_forms = Column(Integer, default=0)
    pending_forms = Column(Integer, default=0)
    
    # Reward tracking
    unique_pages_contributed = Column(Integer, default=0)
    free_weeks_earned = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    
    # Quality metrics
    average_review_score = Column(Float, nullable=True)
    total_downloads = Column(Integer, default=0)
    
    # Timestamps
    last_contribution = Column(DateTime, nullable=True)
    last_reward_granted = Column(DateTime, nullable=True)
    
    # Relationships
    contributor = relationship("User", back_populates="contributor_stats")
    
    def __repr__(self):
        return f"<ContributorStats(contributor_id={self.contributor_id}, approved={self.approved_forms})>"


class RewardLedger(Base, TimestampMixin):
    """Model for tracking reward grants and usage."""
    __tablename__ = "reward_ledger"
    
    id = Column(Integer, primary_key=True, index=True)
    contributor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=True)
    
    # Reward details
    reward_type = Column(String(50), nullable=False)  # "free_week", "premium_access", etc.
    reward_amount = Column(Integer, nullable=False)   # Number of weeks, credits, etc.
    reason = Column(String(255), nullable=True)       # Why reward was granted
    
    # Usage tracking
    granted_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    used_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_used = Column(Boolean, default=False)
    
    # Relationships
    contributor = relationship("User")
    form = relationship("Form")
    
    # Indexes
    __table_args__ = (
        Index('idx_contributor_active', 'contributor_id', 'is_active'),
        Index('idx_expires_active', 'expires_at', 'is_active'),
    )
    
    def __repr__(self):
        return f"<RewardLedger(contributor_id={self.contributor_id}, type={self.reward_type}, amount={self.reward_amount})>"


class FormFeedback(Base, TimestampMixin):
    """Model for user feedback on forms."""
    __tablename__ = "form_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(32), unique=True, index=True, nullable=False)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Feedback content
    feedback_type = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    severity = Column(Integer, default=1)  # 1-5 scale
    
    # Contact and tracking
    contact_email = Column(String(255), nullable=True)
    ticket_number = Column(String(20), unique=True, nullable=True)
    
    # Status and resolution
    status = Column(String(20), default="received", index=True)
    admin_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    form = relationship("Form")
    user = relationship("User", foreign_keys=[user_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_form_feedback_status', 'form_id', 'status'),
        Index('idx_feedback_type_severity', 'feedback_type', 'severity'),
    )
    
    def __repr__(self):
        return f"<FormFeedback(form_id={self.form_id}, type={self.feedback_type}, severity={self.severity})>"
