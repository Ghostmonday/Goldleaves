# models/ai/predicted_field.py
"""AI-predicted form field model with confidence scoring."""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from .dependencies import Base


class ConfidenceLevel(str, Enum):
    """Confidence level categories for AI predictions."""
    HIGH = "high"        # >= 0.9
    MEDIUM = "medium"    # 0.7 - 0.89
    LOW = "low"          # 0.5 - 0.69
    VERY_LOW = "very_low"  # < 0.5


class PredictionStatus(str, Enum):
    """Status of AI prediction."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEWED = "reviewed"
    CORRECTED = "corrected"
    REJECTED = "rejected"


class PredictedField(Base):
    """AI-predicted form field with confidence scoring and validation."""
    
    __tablename__ = "predicted_fields"
    
    # Basic identification
    id = Column(Integer, primary_key=True, index=True)
    prediction_request_id = Column(Integer, ForeignKey("prediction_requests.id"), nullable=False)
    form_id = Column(String(255), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Field information
    field_name = Column(String(255), nullable=False)
    field_type = Column(String(100), nullable=False)
    field_category = Column(String(100), default="text_general")
    field_label = Column(String(500), nullable=True)
    
    # Prediction data
    predicted_value = Column(Text, nullable=True)  # JSON serialized value
    confidence_score = Column(Float, nullable=False)
    confidence_level = Column(String(20), nullable=False)  # ConfidenceLevel enum
    status = Column(String(20), default=PredictionStatus.PENDING.value)
    
    # AI reasoning and metadata
    reasoning = Column(Text, nullable=True)
    model_used = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    processing_time_ms = Column(Integer, default=0)
    
    # Validation results
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(JSON, nullable=True)
    validation_metadata = Column(JSON, nullable=True)
    
    # Review and approval
    requires_review = Column(Boolean, default=False)
    requires_attorney_review = Column(Boolean, default=False)
    auto_fill_disabled = Column(Boolean, default=False)
    human_reviewed = Column(Boolean, default=False)
    human_corrected = Column(Boolean, default=False)
    
    # Review details
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Legal compliance
    disclaimer_shown = Column(Boolean, default=False)
    legal_review_required = Column(Boolean, default=False)
    upv_safeguard_applied = Column(Boolean, default=False)
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    field_metadata = Column(JSON, nullable=True)
    jurisdiction = Column(String(10), nullable=True)
    
    # Relationships
    prediction_request = relationship("PredictionRequest", back_populates="predicted_fields")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    feedback = relationship("PredictionFeedback", back_populates="predicted_field", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PredictedField {self.field_name}={self.predicted_value} (confidence={self.confidence_score})>"
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if prediction has high confidence."""
        return self.confidence_score >= 0.9
    
    @property
    def is_auto_approvable(self) -> bool:
        """Check if prediction can be auto-approved."""
        return (
            self.is_high_confidence and 
            self.is_valid and 
            not self.requires_review and 
            not self.requires_attorney_review
        )
    
    @property
    def needs_human_intervention(self) -> bool:
        """Check if prediction needs human intervention."""
        return (
            self.requires_review or 
            self.requires_attorney_review or 
            not self.is_valid or 
            self.confidence_score < 0.7
        )
    
    def calculate_confidence_level(self) -> ConfidenceLevel:
        """Calculate confidence level based on score."""
        if self.confidence_score >= 0.9:
            return ConfidenceLevel.HIGH
        elif self.confidence_score >= 0.7:
            return ConfidenceLevel.MEDIUM
        elif self.confidence_score >= 0.5:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def apply_upv_safeguards(self, field_metadata: Optional[Dict[str, Any]] = None):
        """Apply Unauthorized Practice of Law safeguards."""
        # Check if field requires attorney review
        attorney_review_patterns = [
            "legal_grounds", "custody_recommendation", "property_division",
            "spousal_support", "legal_strategy", "attorney_", "counsel_"
        ]
        
        if any(pattern in self.field_name.lower() for pattern in attorney_review_patterns):
            self.requires_attorney_review = True
            self.auto_fill_disabled = True
            self.upv_safeguard_applied = True
        
        # Check metadata flags
        if field_metadata:
            if field_metadata.get("legal_critical", False):
                self.requires_attorney_review = True
                self.auto_fill_disabled = True
            
            if field_metadata.get("affects_custody", False):
                self.requires_review = True
            
            if field_metadata.get("financial_disclosure", False):
                self.requires_review = True
        
        self.upv_safeguard_applied = True
    
    def mark_reviewed(self, reviewer_id: int, notes: Optional[str] = None):
        """Mark field as reviewed by human."""
        self.human_reviewed = True
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.review_notes = notes
        self.status = PredictionStatus.REVIEWED.value
    
    def mark_corrected(self, corrected_value: Any, reviewer_id: int):
        """Mark field as corrected by human."""
        self.human_corrected = True
        self.predicted_value = str(corrected_value)
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.status = PredictionStatus.CORRECTED.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "field_name": self.field_name,
            "field_type": self.field_type,
            "predicted_value": self.predicted_value,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level,
            "status": self.status,
            "reasoning": self.reasoning,
            "requires_review": self.requires_review,
            "requires_attorney_review": self.requires_attorney_review,
            "auto_fill_disabled": self.auto_fill_disabled,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "human_reviewed": self.human_reviewed,
            "human_corrected": self.human_corrected,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
