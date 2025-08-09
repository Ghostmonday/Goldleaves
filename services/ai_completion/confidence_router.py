# services/ai_completion/confidence_router.py
"""Routes predictions based on confidence levels."""

from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence levels for predictions."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ConfidenceRouter:
    """Routes predictions based on confidence levels and requirements."""
    
    def __init__(self):
        self.confidence_thresholds = {
            ConfidenceLevel.VERY_HIGH: 0.95,
            ConfidenceLevel.HIGH: 0.85,
            ConfidenceLevel.MEDIUM: 0.70,
            ConfidenceLevel.LOW: 0.50,
            ConfidenceLevel.VERY_LOW: 0.0
        }
    
    def determine_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """Determine confidence level from score."""
        if confidence_score >= self.confidence_thresholds[ConfidenceLevel.VERY_HIGH]:
            return ConfidenceLevel.VERY_HIGH
        elif confidence_score >= self.confidence_thresholds[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif confidence_score >= self.confidence_thresholds[ConfidenceLevel.MEDIUM]:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= self.confidence_thresholds[ConfidenceLevel.LOW]:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def requires_review(self, confidence_score: float, field_type: str = "text") -> bool:
        """Determine if a prediction requires human review."""
        # Always require review for legal/financial fields below high confidence
        sensitive_fields = ["legal", "financial", "personal_info", "signature"]
        
        if field_type in sensitive_fields:
            return confidence_score < self.confidence_thresholds[ConfidenceLevel.HIGH]
        
        # For other fields, require review below medium confidence
        return confidence_score < self.confidence_thresholds[ConfidenceLevel.MEDIUM]
    
    def should_auto_apply(self, confidence_score: float, field_type: str = "text") -> bool:
        """Determine if prediction can be auto-applied."""
        # Never auto-apply sensitive fields
        sensitive_fields = ["legal", "financial", "personal_info", "signature"]
        
        if field_type in sensitive_fields:
            return False
        
        # Auto-apply high confidence non-sensitive predictions
        return confidence_score >= self.confidence_thresholds[ConfidenceLevel.HIGH]
