# models/ai/prediction_response.py
"""AI prediction response model for form completion results."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship

from .dependencies import Base


class ResponseType(str, Enum):
    """Type of prediction response."""
    FIELD_PREDICTION = "field_prediction"
    FORM_ANALYSIS = "form_analysis"
    VALIDATION_RESULT = "validation_result"
    CONFIDENCE_ASSESSMENT = "confidence_assessment"
    ERROR_RESPONSE = "error_response"


class ResponseStatus(str, Enum):
    """Status of prediction response."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    WARNING = "warning"
    ERROR = "error"
    TIMEOUT = "timeout"


class PredictionResponse(Base):
    """AI prediction response with detailed results and metadata."""
    
    __tablename__ = "prediction_responses"
    
    # Basic identification
    id = Column(Integer, primary_key=True, index=True)
    prediction_request_id = Column(Integer, ForeignKey("prediction_requests.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Response metadata
    response_type = Column(String(50), default=ResponseType.FIELD_PREDICTION.value)
    status = Column(String(20), default=ResponseStatus.SUCCESS.value)
    
    # Model information
    model_used = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)
    provider = Column(String(50), nullable=True)  # openai, anthropic, local
    
    # Request processing
    prompt_text = Column(Text, nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Response data
    raw_response = Column(Text, nullable=True)  # Raw AI response
    parsed_response = Column(JSON, nullable=True)  # Structured response
    structured_predictions = Column(JSON, nullable=True)  # Final field predictions
    
    # Confidence and validation
    overall_confidence = Column(Float, default=0.0)
    confidence_breakdown = Column(JSON, nullable=True)  # Per-field confidence
    validation_results = Column(JSON, nullable=True)
    quality_score = Column(Float, default=0.0)
    
    # Processing metrics
    processing_time_ms = Column(Integer, default=0)
    api_latency_ms = Column(Integer, default=0)
    parsing_time_ms = Column(Integer, default=0)
    validation_time_ms = Column(Integer, default=0)
    
    # Error handling
    has_errors = Column(Boolean, default=False)
    error_count = Column(Integer, default=0)
    errors = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    
    # Success metrics
    successful_predictions = Column(Integer, default=0)
    failed_predictions = Column(Integer, default=0)
    skipped_fields = Column(Integer, default=0)
    
    # Cost tracking
    cost_estimate = Column(Float, default=0.0)
    cost_currency = Column(String(10), default="USD")
    cost_breakdown = Column(JSON, nullable=True)
    
    # Legal compliance
    upv_warnings = Column(JSON, nullable=True)
    attorney_review_flags = Column(JSON, nullable=True)
    compliance_notes = Column(Text, nullable=True)
    
    # Response quality indicators
    hallucination_detected = Column(Boolean, default=False)
    consistency_score = Column(Float, default=1.0)
    relevance_score = Column(Float, default=1.0)
    completeness_score = Column(Float, default=1.0)
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    response_metadata = Column(JSON, nullable=True)
    debug_info = Column(JSON, nullable=True)
    
    # Relationships
    prediction_request = relationship("PredictionRequest", back_populates="prediction_responses")
    user = relationship("User")
    
    def __repr__(self):
        return f"<PredictionResponse {self.id} for request {self.prediction_request_id}>"
    
    @property
    def is_successful(self) -> bool:
        """Check if response is successful."""
        return self.status in [ResponseStatus.SUCCESS.value, ResponseStatus.PARTIAL_SUCCESS.value]
    
    @property
    def has_warnings(self) -> bool:
        """Check if response has warnings."""
        return bool(self.warnings) or self.status == ResponseStatus.WARNING.value
    
    @property
    def success_rate(self) -> float:
        """Calculate prediction success rate."""
        total = self.successful_predictions + self.failed_predictions
        if total == 0:
            return 0.0
        return (self.successful_predictions / total) * 100
    
    @property
    def tokens_per_second(self) -> float:
        """Calculate token processing speed."""
        if self.processing_time_ms == 0:
            return 0.0
        return (self.total_tokens / self.processing_time_ms) * 1000
    
    @property
    def cost_per_token(self) -> float:
        """Calculate cost per token."""
        if self.total_tokens == 0:
            return 0.0
        return self.cost_estimate / self.total_tokens
    
    def add_error(self, field_name: str, error_message: str, error_type: str = "validation"):
        """Add an error to the response."""
        if not self.errors:
            self.errors = []
        
        error = {
            "field": field_name,
            "message": error_message,
            "type": error_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.errors.append(error)
        self.error_count = len(self.errors)
        self.has_errors = True
        
        if self.status == ResponseStatus.SUCCESS.value:
            self.status = ResponseStatus.PARTIAL_SUCCESS.value
    
    def add_warning(self, field_name: str, warning_message: str, warning_type: str = "confidence"):
        """Add a warning to the response."""
        if not self.warnings:
            self.warnings = []
        
        warning = {
            "field": field_name,
            "message": warning_message,
            "type": warning_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.warnings.append(warning)
    
    def add_upv_warning(self, field_name: str, warning_message: str):
        """Add UPV (Unauthorized Practice of Law) warning."""
        if not self.upv_warnings:
            self.upv_warnings = []
        
        warning = {
            "field": field_name,
            "message": warning_message,
            "timestamp": datetime.utcnow().isoformat(),
            "requires_attorney_review": True
        }
        
        self.upv_warnings.append(warning)
    
    def flag_attorney_review(self, field_name: str, reason: str):
        """Flag field for attorney review."""
        if not self.attorney_review_flags:
            self.attorney_review_flags = []
        
        flag = {
            "field": field_name,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "high"
        }
        
        self.attorney_review_flags.append(flag)
    
    def calculate_quality_score(self) -> float:
        """Calculate overall quality score."""
        scores = []
        
        # Confidence score (0-1)
        scores.append(self.overall_confidence)
        
        # Success rate (0-1)
        scores.append(self.success_rate / 100)
        
        # Consistency score
        scores.append(self.consistency_score)
        
        # Relevance score
        scores.append(self.relevance_score)
        
        # Completeness score
        scores.append(self.completeness_score)
        
        # Penalty for errors
        if self.has_errors:
            error_penalty = min(0.3, self.error_count * 0.1)
            scores.append(1.0 - error_penalty)
        
        # Penalty for hallucinations
        if self.hallucination_detected:
            scores.append(0.5)
        
        if not scores:
            return 0.0
        
        self.quality_score = sum(scores) / len(scores)
        return self.quality_score
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return {
            "processing_time_ms": self.processing_time_ms,
            "api_latency_ms": self.api_latency_ms,
            "total_tokens": self.total_tokens,
            "tokens_per_second": self.tokens_per_second,
            "cost_estimate": self.cost_estimate,
            "cost_per_token": self.cost_per_token,
            "success_rate": self.success_rate,
            "quality_score": self.quality_score,
            "overall_confidence": self.overall_confidence
        }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error and warning summary."""
        return {
            "has_errors": self.has_errors,
            "error_count": self.error_count,
            "warning_count": len(self.warnings) if self.warnings else 0,
            "upv_warning_count": len(self.upv_warnings) if self.upv_warnings else 0,
            "attorney_review_flags": len(self.attorney_review_flags) if self.attorney_review_flags else 0,
            "hallucination_detected": self.hallucination_detected
        }
    
    def get_field_predictions(self) -> List[Dict[str, Any]]:
        """Get structured field predictions."""
        if not self.structured_predictions:
            return []
        
        predictions = []
        for field_data in self.structured_predictions:
            prediction = {
                "field_name": field_data.get("field_name"),
                "predicted_value": field_data.get("predicted_value"),
                "confidence": field_data.get("confidence"),
                "reasoning": field_data.get("reasoning"),
                "requires_review": field_data.get("requires_review", False),
                "validation_status": field_data.get("validation_status", "unknown")
            }
            predictions.append(prediction)
        
        return predictions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "prediction_request_id": self.prediction_request_id,
            "status": self.status,
            "response_type": self.response_type,
            "model_used": self.model_used,
            "overall_confidence": self.overall_confidence,
            "successful_predictions": self.successful_predictions,
            "failed_predictions": self.failed_predictions,
            "performance_summary": self.get_performance_summary(),
            "error_summary": self.get_error_summary(),
            "field_predictions": self.get_field_predictions(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "upv_warnings": self.upv_warnings,
            "attorney_review_flags": self.attorney_review_flags
        }
