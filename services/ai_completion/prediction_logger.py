# services/ai_completion/prediction_logger.py
"""Logs prediction metrics and performance data."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PredictionLogger:
    """Logs and tracks prediction performance metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def log_prediction_metrics(
        self,
        request,  # PredictionRequest object
        response,  # PredictionResponse object  
        predicted_fields: List  # List of PredictedField objects
    ):
        """Log metrics for a prediction request."""
        try:
            # Calculate metrics
            metrics = self._calculate_metrics(request, response, predicted_fields)
            
            # Log performance data
            logger.info(
                f"Prediction metrics for request {request.id}: "
                f"fields={metrics['total_fields']}, "
                f"avg_confidence={metrics['avg_confidence']:.3f}, "
                f"processing_time={metrics['processing_time']}ms"
            )
            
            # Store metrics in database if needed
            # (Implementation depends on your metrics storage strategy)
            
        except Exception as e:
            logger.error(f"Error logging prediction metrics: {e}")
    
    def _calculate_metrics(self, request, response, predicted_fields: List) -> Dict[str, Any]:
        """Calculate performance metrics."""
        from builtins import len, sum
        
        if not predicted_fields:
            return {
                "total_fields": 0,
                "avg_confidence": 0.0,
                "processing_time": response.processing_time_ms if response else 0
            }
        
        confidence_scores = [field.confidence_score for field in predicted_fields]
        
        return {
            "total_fields": len(predicted_fields),
            "avg_confidence": sum(confidence_scores) / len(confidence_scores),
            "high_confidence_count": len([f for f in predicted_fields if f.confidence_score >= 0.8]),
            "requires_review_count": len([f for f in predicted_fields if f.requires_review]),
            "processing_time": response.processing_time_ms if response else 0,
            "token_usage": response.total_tokens if response else 0
        }
    
    async def log_field_validation(self, field_name: str, is_valid: bool, errors: List[str] = None):
        """Log field validation results."""
        logger.debug(f"Field validation - {field_name}: valid={is_valid}, errors={errors or []}")
    
    async def log_model_performance(self, model_name: str, response_time_ms: int, token_count: int):
        """Log model performance metrics."""
        logger.info(f"Model performance - {model_name}: {response_time_ms}ms, {token_count} tokens")
