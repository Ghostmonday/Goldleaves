# models/ai/feedback.py
"""User feedback model for AI prediction quality and improvement."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .dependencies import Base


class FeedbackType(str, Enum):
    """Type of feedback provided by user."""
    ACCURACY = "accuracy"              # Feedback on prediction accuracy
    RELEVANCE = "relevance"            # Feedback on prediction relevance
    CONFIDENCE = "confidence"          # Feedback on confidence levels
    COMPLETENESS = "completeness"      # Feedback on response completeness
    USABILITY = "usability"            # Feedback on user experience
    PERFORMANCE = "performance"        # Feedback on system performance
    BUG_REPORT = "bug_report"         # Bug or error reports
    FEATURE_REQUEST = "feature_request" # Feature improvement requests
    GENERAL = "general"                # General feedback


class FeedbackPriority(str, Enum):
    """Priority level for feedback processing."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SentimentType(str, Enum):
    """Sentiment of the feedback."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class FeedbackStatus(str, Enum):
    """Status of feedback processing."""
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"


class PredictionFeedback(Base):
    """User feedback on AI predictions for continuous improvement."""

    __tablename__ = "prediction_feedback"

    # Basic identification
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prediction_request_id = Column(Integer, ForeignKey("prediction_requests.id"), nullable=True)
    predicted_field_id = Column(Integer, ForeignKey("predicted_fields.id"), nullable=True)

    # Feedback metadata
    feedback_type = Column(String(50), nullable=False)
    priority = Column(String(20), default=FeedbackPriority.MEDIUM.value)
    status = Column(String(20), default=FeedbackStatus.SUBMITTED.value)
    sentiment = Column(String(20), nullable=True)

    # Feedback content
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    feedback_text = Column(Text, nullable=False)

    # Ratings (1-5 scale)
    accuracy_rating = Column(Integer, nullable=True)      # How accurate was the prediction?
    relevance_rating = Column(Integer, nullable=True)     # How relevant was the prediction?
    confidence_rating = Column(Integer, nullable=True)    # How confident are you in this rating?
    usability_rating = Column(Integer, nullable=True)     # How easy was it to use?
    overall_rating = Column(Integer, nullable=True)       # Overall satisfaction

    # Specific prediction feedback
    was_prediction_correct = Column(Boolean, nullable=True)
    was_prediction_helpful = Column(Boolean, nullable=True)
    would_use_again = Column(Boolean, nullable=True)

    # Improvement suggestions
    suggested_value = Column(Text, nullable=True)          # What should the value have been?
    improvement_suggestions = Column(Text, nullable=True)
    feature_requests = Column(JSON, nullable=True)

    # Context information
    form_context = Column(JSON, nullable=True)             # Context about the form
    user_context = Column(JSON, nullable=True)             # Context about user situation
    session_context = Column(JSON, nullable=True)          # Context about the session

    # Technical details
    browser_info = Column(JSON, nullable=True)
    device_info = Column(JSON, nullable=True)
    performance_metrics = Column(JSON, nullable=True)

    # Processing information
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Resolution tracking
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolution_actions = Column(JSON, nullable=True)

    # Impact tracking
    helped_improve_model = Column(Boolean, default=False)
    led_to_bug_fix = Column(Boolean, default=False)
    led_to_feature = Column(Boolean, default=False)
    impact_score = Column(Float, default=0.0)

    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    follow_up_notes = Column(Text, nullable=True)

    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Additional metadata
    feedback_metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    resolver = relationship("User", foreign_keys=[resolved_by])
    prediction_request = relationship("PredictionRequest", back_populates="feedback")
    predicted_field = relationship("PredictedField", back_populates="feedback")

    def __repr__(self):
        return f"<PredictionFeedback {self.id} by user {self.user_id} ({self.feedback_type})>"

    @property
    def is_positive(self) -> bool:
        """Check if feedback is positive."""
        if self.sentiment:
            return self.sentiment == SentimentType.POSITIVE.value

        # Infer from ratings
        ratings = [r for r in [self.accuracy_rating, self.relevance_rating, self.overall_rating] if r is not None]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            return avg_rating >= 4

        return False

    @property
    def is_negative(self) -> bool:
        """Check if feedback is negative."""
        if self.sentiment:
            return self.sentiment == SentimentType.NEGATIVE.value

        # Infer from ratings
        ratings = [r for r in [self.accuracy_rating, self.relevance_rating, self.overall_rating] if r is not None]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            return avg_rating <= 2

        return False

    @property
    def needs_attention(self) -> bool:
        """Check if feedback needs immediate attention."""
        return (
            self.priority in [FeedbackPriority.HIGH.value, FeedbackPriority.CRITICAL.value] or
            self.is_negative or
            self.feedback_type == FeedbackType.BUG_REPORT.value
        )

    @property
    def average_rating(self) -> Optional[float]:
        """Calculate average rating across all rating fields."""
        ratings = [
            r for r in [
                self.accuracy_rating, self.relevance_rating,
                self.usability_rating, self.overall_rating
            ] if r is not None
        ]

        if not ratings:
            return None

        return sum(ratings) / len(ratings)

    def detect_sentiment(self) -> SentimentType:
        """Detect sentiment from ratings and feedback text."""
        # Use ratings if available
        avg_rating = self.average_rating
        if avg_rating is not None:
            if avg_rating >= 4:
                return SentimentType.POSITIVE
            elif avg_rating <= 2:
                return SentimentType.NEGATIVE
            else:
                return SentimentType.NEUTRAL

        # Use boolean indicators
        positive_indicators = [
            self.was_prediction_correct,
            self.was_prediction_helpful,
            self.would_use_again
        ]

        positive_count = sum(1 for indicator in positive_indicators if indicator is True)
        negative_count = sum(1 for indicator in positive_indicators if indicator is False)

        if positive_count > negative_count:
            return SentimentType.POSITIVE
        elif negative_count > positive_count:
            return SentimentType.NEGATIVE
        else:
            return SentimentType.NEUTRAL

    def calculate_impact_score(self) -> float:
        """Calculate impact score based on feedback content and outcomes."""
        score = 0.0

        # Base score from ratings
        if self.average_rating:
            score += self.average_rating * 0.2

        # Bonus for specific improvements
        if self.helped_improve_model:
            score += 2.0

        if self.led_to_bug_fix:
            score += 1.5

        if self.led_to_feature:
            score += 1.0

        # Priority weight
        priority_weights = {
            FeedbackPriority.LOW.value: 0.5,
            FeedbackPriority.MEDIUM.value: 1.0,
            FeedbackPriority.HIGH.value: 1.5,
            FeedbackPriority.CRITICAL.value: 2.0
        }
        score *= priority_weights.get(self.priority, 1.0)

        # Type weight
        type_weights = {
            FeedbackType.BUG_REPORT.value: 2.0,
            FeedbackType.ACCURACY.value: 1.5,
            FeedbackType.FEATURE_REQUEST.value: 1.2,
            FeedbackType.PERFORMANCE.value: 1.1,
            FeedbackType.USABILITY.value: 1.0,
            FeedbackType.GENERAL.value: 0.8
        }
        score *= type_weights.get(self.feedback_type, 1.0)

        self.impact_score = min(score, 10.0)  # Cap at 10
        return self.impact_score

    def mark_reviewed(self, reviewer_id: int, notes: Optional[str] = None):
        """Mark feedback as reviewed."""
        self.status = FeedbackStatus.REVIEWED.value
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.review_notes = notes

    def mark_resolved(self, resolver_id: int, notes: Optional[str] = None, actions: Optional[List[str]] = None):
        """Mark feedback as resolved."""
        self.status = FeedbackStatus.RESOLVED.value
        self.resolved_by = resolver_id
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = notes
        if actions:
            self.resolution_actions = actions

    def add_follow_up(self, follow_up_date: datetime, notes: str):
        """Schedule follow-up for this feedback."""
        self.follow_up_required = True
        self.follow_up_date = follow_up_date
        self.follow_up_notes = notes

    def add_tag(self, tag: str):
        """Add a tag to categorize the feedback."""
        if not self.tags:
            self.tags = []

        if tag not in self.tags:
            self.tags.append(tag)

    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of feedback for reporting."""
        return {
            "feedback_type": self.feedback_type,
            "priority": self.priority,
            "sentiment": self.sentiment or self.detect_sentiment().value,
            "average_rating": self.average_rating,
            "was_helpful": self.was_prediction_helpful,
            "would_use_again": self.would_use_again,
            "impact_score": self.impact_score,
            "needs_attention": self.needs_attention,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "feedback_type": self.feedback_type,
            "title": self.title,
            "feedback_text": self.feedback_text,
            "priority": self.priority,
            "status": self.status,
            "sentiment": self.sentiment,
            "ratings": {
                "accuracy": self.accuracy_rating,
                "relevance": self.relevance_rating,
                "usability": self.usability_rating,
                "overall": self.overall_rating,
                "average": self.average_rating
            },
            "prediction_feedback": {
                "was_correct": self.was_prediction_correct,
                "was_helpful": self.was_prediction_helpful,
                "would_use_again": self.would_use_again
            },
            "impact_score": self.impact_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "tags": self.tags
        }
