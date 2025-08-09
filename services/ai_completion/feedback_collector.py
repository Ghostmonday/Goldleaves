# services/ai_completion/feedback_collector.py
"""Collects and processes user feedback on AI predictions."""


import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types of feedback that can be collected."""
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIALLY_CORRECT = "partially_correct"
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    NEEDS_REVIEW = "needs_review"


class FeedbackSeverity(str, Enum):
    """Severity levels for feedback."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackCollector:
    """Collects and processes user feedback on AI predictions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def collect_field_feedback(
        self,
        user_id: str,
        prediction_id: int,
        field_name: str,
        feedback_type: FeedbackType,
        corrected_value: Optional[str] = None,
        comments: Optional[str] = None,
        severity: FeedbackSeverity = FeedbackSeverity.MEDIUM
    ) -> Dict[str, Any]:
        """
        Collect feedback on a specific field prediction.
        
        Args:
            user_id: ID of the user providing feedback
            prediction_id: ID of the prediction being reviewed
            field_name: Name of the field being reviewed
            feedback_type: Type of feedback
            corrected_value: Corrected value if prediction was wrong
            comments: Additional user comments
            severity: Severity level of the feedback
            
        Returns:
            Feedback record dictionary
        """
        try:
            feedback_record = {
                "id": self._generate_feedback_id(),
                "user_id": user_id,
                "prediction_id": prediction_id,
                "field_name": field_name,
                "feedback_type": feedback_type.value,
                "corrected_value": corrected_value,
                "comments": comments,
                "severity": severity.value,
                "created_at": datetime.utcnow().isoformat(),
                "processed": False
            }
            
            # Store feedback (implementation depends on your storage strategy)
            await self._store_feedback(feedback_record)
            
            # Log the feedback
            logger.info(
                f"Collected feedback for prediction {prediction_id}, "
                f"field {field_name}: {feedback_type.value}"
            )
            
            # Trigger improvement processes if needed
            if feedback_type in [FeedbackType.INCORRECT, FeedbackType.NOT_HELPFUL]:
                await self._trigger_model_improvement(feedback_record)
            
            return feedback_record
            
        except Exception as e:
            logger.error(f"Error collecting feedback: {e}")
            raise
    
    async def collect_prediction_feedback(
        self,
        user_id: str,
        prediction_id: int,
        overall_rating: int,  # 1-5 scale
        feedback_type: FeedbackType,
        comments: Optional[str] = None,
        field_feedback: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Collect overall feedback on a prediction request.
        
        Args:
            user_id: ID of the user providing feedback
            prediction_id: ID of the prediction being reviewed
            overall_rating: Overall rating (1-5)
            feedback_type: Type of feedback
            comments: User comments
            field_feedback: Individual field feedback
            
        Returns:
            Feedback summary
        """
        try:
            feedback_summary = {
                "id": self._generate_feedback_id(),
                "user_id": user_id,
                "prediction_id": prediction_id,
                "overall_rating": overall_rating,
                "feedback_type": feedback_type.value,
                "comments": comments,
                "field_feedback_count": len(field_feedback) if field_feedback else 0,
                "created_at": datetime.utcnow().isoformat(),
                "processed": False
            }
            
            # Process individual field feedback if provided
            if field_feedback:
                for field_fb in field_feedback:
                    await self.collect_field_feedback(
                        user_id=user_id,
                        prediction_id=prediction_id,
                        field_name=field_fb.get("field_name"),
                        feedback_type=FeedbackType(field_fb.get("feedback_type")),
                        corrected_value=field_fb.get("corrected_value"),
                        comments=field_fb.get("comments"),
                        severity=FeedbackSeverity(field_fb.get("severity", "medium"))
                    )
            
            # Store overall feedback
            await self._store_feedback(feedback_summary)
            
            logger.info(f"Collected overall feedback for prediction {prediction_id}: rating {overall_rating}")
            
            return feedback_summary
            
        except Exception as e:
            logger.error(f"Error collecting prediction feedback: {e}")
            raise
    
    async def get_feedback_summary(self, prediction_id: int) -> Dict[str, Any]:
        """Get feedback summary for a prediction."""
        # Implementation would retrieve feedback from storage
        return {
            "prediction_id": prediction_id,
            "total_feedback": 0,
            "average_rating": 0.0,
            "feedback_types": {},
            "field_feedback": []
        }
    
    async def process_feedback_for_training(self) -> Dict[str, Any]:
        """Process collected feedback for model training improvements."""
        try:
            # Get unprocessed feedback
            feedback_data = await self._get_unprocessed_feedback()
            
            # Analyze feedback patterns
            analysis = self._analyze_feedback_patterns(feedback_data)
            
            # Generate training recommendations
            recommendations = self._generate_training_recommendations(analysis)
            
            # Mark feedback as processed
            await self._mark_feedback_processed(feedback_data)
            
            logger.info(f"Processed {len(feedback_data)} feedback items for training")
            
            return {
                "processed_count": len(feedback_data),
                "analysis": analysis,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error processing feedback for training: {e}")
            raise
    
    def _generate_feedback_id(self) -> str:
        """Generate unique feedback ID."""
        import uuid
        return str(uuid.uuid4())
    
    async def _store_feedback(self, feedback_record: Dict[str, Any]):
        """Store feedback record."""
        # Implementation depends on your storage strategy
        # Could be database, file, or external service
        logger.debug(f"Storing feedback record: {feedback_record['id']}")
    
    async def _trigger_model_improvement(self, feedback_record: Dict[str, Any]):
        """Trigger model improvement processes based on negative feedback."""
        logger.info(f"Triggering model improvement for feedback: {feedback_record['id']}")
        # Implementation would trigger retraining or model adjustment
    
    async def _get_unprocessed_feedback(self) -> List[Dict[str, Any]]:
        """Get unprocessed feedback records."""
        # Implementation would query storage for unprocessed feedback
        return []
    
    def _analyze_feedback_patterns(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze feedback patterns for insights."""
        
        if not feedback_data:
            return {"total": 0, "patterns": []}
        
        # Basic analysis
        feedback_types = {}
        for feedback in feedback_data:
            fb_type = feedback.get("feedback_type", "unknown")
            feedback_types[fb_type] = feedback_types.get(fb_type, 0) + 1
        
        return {
            "total": len(feedback_data),
            "feedback_types": feedback_types,
            "patterns": []  # More sophisticated pattern analysis would go here
        }
    
    def _generate_training_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for model training based on analysis."""
        recommendations = []
        
        feedback_types = analysis.get("feedback_types", {})
        
        # Generate recommendations based on feedback patterns
        if feedback_types.get("incorrect", 0) > 5:
            recommendations.append("Consider retraining model with additional data")
        
        if feedback_types.get("not_helpful", 0) > 3:
            recommendations.append("Review prompt engineering and response formatting")
        
        if feedback_types.get("needs_review", 0) > 10:
            recommendations.append("Adjust confidence thresholds to reduce auto-application")
        
        return recommendations
    
    async def _mark_feedback_processed(self, feedback_data: List[Dict[str, Any]]):
        """Mark feedback records as processed."""
        logger.debug(f"Marking {len(feedback_data)} feedback records as processed")
        # Implementation would update storage to mark records as processed
