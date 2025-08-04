# models/ai/prediction_request.py
"""AI prediction request model for form completion sessions."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship

from .dependencies import Base


class RequestStatus(str, Enum):
    """Status of prediction request."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class RequestPriority(str, Enum):
    """Priority level for prediction requests."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class PredictionRequest(Base):
    """AI prediction request for form completion."""
    
    __tablename__ = "prediction_requests"
    
    # Basic identification
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    form_id = Column(String(255), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Request metadata
    request_type = Column(String(50), default="form_completion")
    priority = Column(String(20), default=RequestPriority.NORMAL.value)
    status = Column(String(20), default=RequestStatus.PENDING.value)
    
    # Form data and context
    form_schema = Column(JSON, nullable=True)  # Form structure
    existing_data = Column(JSON, nullable=True)  # Pre-filled data
    context_data = Column(JSON, nullable=True)  # User context
    field_requirements = Column(JSON, nullable=True)  # Specific field rules
    
    # Processing configuration
    requested_fields = Column(JSON, nullable=True)  # List of fields to predict
    prediction_mode = Column(String(50), default="standard")  # standard, conservative, aggressive
    confidence_threshold = Column(Float, default=0.7)
    enable_auto_fill = Column(Boolean, default=True)
    
    # Model configuration
    model_preference = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)
    temperature = Column(Float, default=0.3)
    max_tokens = Column(Integer, default=1000)
    
    # Processing details
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processing_time_ms = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)
    
    # Results summary
    total_fields_requested = Column(Integer, default=0)
    total_fields_predicted = Column(Integer, default=0)
    high_confidence_count = Column(Integer, default=0)
    medium_confidence_count = Column(Integer, default=0)
    low_confidence_count = Column(Integer, default=0)
    failed_predictions = Column(Integer, default=0)
    
    # Quality metrics
    average_confidence = Column(Float, default=0.0)
    validation_pass_rate = Column(Float, default=0.0)
    auto_approval_rate = Column(Float, default=0.0)
    review_required_count = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Legal compliance
    jurisdiction = Column(String(10), nullable=True)
    upv_safeguards_enabled = Column(Boolean, default=True)
    attorney_review_flagged = Column(Boolean, default=False)
    disclaimer_required = Column(Boolean, default=True)
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Request source tracking
    source_ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    source_platform = Column(String(50), nullable=True)  # web, mobile, api
    
    # Additional metadata
    request_metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="prediction_requests")
    document = relationship("Document", back_populates="prediction_requests")
    predicted_fields = relationship("PredictedField", back_populates="prediction_request", cascade="all, delete-orphan")
    feedback = relationship("PredictionFeedback", back_populates="prediction_request", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PredictionRequest {self.id} for form {self.form_id} by user {self.user_id}>"
    
    @property
    def is_processing(self) -> bool:
        """Check if request is currently processing."""
        return self.status == RequestStatus.PROCESSING.value
    
    @property
    def is_completed(self) -> bool:
        """Check if request is completed."""
        return self.status == RequestStatus.COMPLETED.value
    
    @property
    def is_failed(self) -> bool:
        """Check if request failed."""
        return self.status in [RequestStatus.FAILED.value, RequestStatus.TIMEOUT.value]
    
    @property
    def can_retry(self) -> bool:
        """Check if request can be retried."""
        return self.retry_count < self.max_retries and self.is_failed
    
    @property
    def success_rate(self) -> float:
        """Calculate prediction success rate."""
        if self.total_fields_requested == 0:
            return 0.0
        return (self.total_fields_predicted / self.total_fields_requested) * 100
    
    @property
    def high_confidence_rate(self) -> float:
        """Calculate high confidence prediction rate."""
        if self.total_fields_predicted == 0:
            return 0.0
        return (self.high_confidence_count / self.total_fields_predicted) * 100
    
    def start_processing(self):
        """Mark request as started."""
        self.status = RequestStatus.PROCESSING.value
        self.started_at = datetime.utcnow()
    
    def complete_processing(self):
        """Mark request as completed and calculate metrics."""
        self.status = RequestStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.processing_time_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        
        # Calculate summary metrics
        if self.predicted_fields:
            self.total_fields_predicted = len(self.predicted_fields)
            
            confidence_scores = [field.confidence_score for field in self.predicted_fields]
            self.average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            self.high_confidence_count = sum(1 for field in self.predicted_fields if field.confidence_score >= 0.9)
            self.medium_confidence_count = sum(1 for field in self.predicted_fields if 0.7 <= field.confidence_score < 0.9)
            self.low_confidence_count = sum(1 for field in self.predicted_fields if field.confidence_score < 0.7)
            
            valid_predictions = sum(1 for field in self.predicted_fields if field.is_valid)
            self.validation_pass_rate = (valid_predictions / self.total_fields_predicted) * 100 if self.total_fields_predicted > 0 else 0.0
            
            auto_approved = sum(1 for field in self.predicted_fields if field.is_auto_approvable)
            self.auto_approval_rate = (auto_approved / self.total_fields_predicted) * 100 if self.total_fields_predicted > 0 else 0.0
            
            self.review_required_count = sum(1 for field in self.predicted_fields if field.needs_human_intervention)
    
    def fail_processing(self, error_message: str, error_details: Optional[Dict[str, Any]] = None):
        """Mark request as failed."""
        self.status = RequestStatus.FAILED.value
        self.error_message = error_message
        self.error_details = error_details
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.processing_time_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
    
    def retry_request(self):
        """Prepare request for retry."""
        if not self.can_retry:
            raise ValueError("Request cannot be retried")
        
        self.retry_count += 1
        self.status = RequestStatus.PENDING.value
        self.error_message = None
        self.error_details = None
        self.started_at = None
        self.completed_at = None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the request."""
        return {
            "processing_time_ms": self.processing_time_ms,
            "total_tokens_used": self.total_tokens_used,
            "cost_estimate": self.cost_estimate,
            "success_rate": self.success_rate,
            "average_confidence": self.average_confidence,
            "high_confidence_rate": self.high_confidence_rate,
            "validation_pass_rate": self.validation_pass_rate,
            "auto_approval_rate": self.auto_approval_rate,
            "review_required_count": self.review_required_count,
            "retry_count": self.retry_count
        }
    
    def get_field_distribution(self) -> Dict[str, int]:
        """Get distribution of field confidence levels."""
        return {
            "high_confidence": self.high_confidence_count,
            "medium_confidence": self.medium_confidence_count,
            "low_confidence": self.low_confidence_count,
            "failed": self.failed_predictions
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "form_id": self.form_id,
            "status": self.status,
            "priority": self.priority,
            "total_fields_requested": self.total_fields_requested,
            "total_fields_predicted": self.total_fields_predicted,
            "average_confidence": self.average_confidence,
            "processing_time_ms": self.processing_time_ms,
            "review_required_count": self.review_required_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "performance_metrics": self.get_performance_metrics(),
            "field_distribution": self.get_field_distribution()
        }
