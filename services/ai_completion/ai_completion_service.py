# services/ai_completion/ai_completion_service.py
"""Core AI completion service for form prediction."""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from builtins import len, locals, filter, sum
import openai
from sqlalchemy.orm import Session

from models.ai import (
    PredictedField, PredictionRequest, PredictionResponse,
    ConfidenceLevel, PredictionStatus, RequestStatus, ResponseStatus
)
from core.config import settings
from core.logging import get_logger
from .confidence_router import ConfidenceRouter
from .prediction_logger import PredictionLogger

logger = get_logger(__name__)


class PredictionMode(str, Enum):
    """Prediction modes for different use cases."""
    STANDARD = "standard"      # Balanced accuracy and speed
    CONSERVATIVE = "conservative"  # High confidence, fewer predictions
    AGGRESSIVE = "aggressive"   # More predictions, lower confidence threshold
    BULK = "bulk"              # Optimized for batch processing


class AICompletionService:
    """Service for AI-powered form completion and prediction."""
    
    def __init__(self, db: Session):
        self.db = db
        self.confidence_router = ConfidenceRouter()
        self.prediction_logger = PredictionLogger(db)
        
        # Model configuration
        self.model_name = settings.AI_MODEL_NAME or "gpt-4"
        self.temperature = 0.3
        self.max_tokens = 1000
        
        # Prediction thresholds
        self.confidence_thresholds = {
            PredictionMode.CONSERVATIVE: 0.9,
            PredictionMode.STANDARD: 0.7,
            PredictionMode.AGGRESSIVE: 0.5,
            PredictionMode.BULK: 0.6
        }
        
        # Initialize OpenAI client
        openai.api_key = settings.OPENAI_API_KEY
    
    async def predict_form_fields(
        self,
        request: PredictionRequest,
        form_schema: Dict[str, Any],
        existing_data: Optional[Dict[str, Any]] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> PredictionResponse:
        """
        Predict form field values using AI.
        
        Args:
            request: The prediction request object
            form_schema: Schema definition of the form
            existing_data: Pre-filled form data
            context_data: Additional context (user profile, document data, etc.)
            
        Returns:
            PredictionResponse with predicted field values
        """
        try:
            # Start processing
            request.start_processing()
            self.db.commit()
            
            # Create response object
            response = PredictionResponse(
                prediction_request_id=request.id,
                user_id=request.user_id,
                model_used=self.model_name,
                model_version="1.0",
                provider="openai"
            )
            
            start_time = datetime.utcnow()
            
            # Extract fields to predict
            fields_to_predict = self._extract_predictable_fields(
                form_schema, existing_data, request.requested_fields
            )
            
            if not fields_to_predict:
                response.status = ResponseStatus.WARNING.value
                response.errors = [{"message": "No predictable fields found", "type": "validation"}]
                self.db.add(response)
                self.db.commit()
                return response
            
            # Build prediction prompt
            prompt = self._build_prediction_prompt(
                fields_to_predict, form_schema, existing_data, context_data
            )
            
            # Get AI prediction
            ai_response_data = await self._call_ai_model(prompt, request.temperature or self.temperature)
            
            # Parse AI response
            parsed_predictions = self._parse_ai_response(ai_response_data["content"])
            
            # Create predicted field objects
            predicted_fields = []
            for field_name, prediction_data in parsed_predictions.items():
                if field_name in fields_to_predict:
                    predicted_field = await self._create_predicted_field(
                        request, field_name, prediction_data, form_schema
                    )
                    predicted_fields.append(predicted_field)
            
            # Update response with results
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            response.processing_time_ms = int(processing_time)
            response.prompt_tokens = ai_response_data.get("prompt_tokens", 0)
            response.completion_tokens = ai_response_data.get("completion_tokens", 0)
            response.total_tokens = response.prompt_tokens + response.completion_tokens
            response.raw_response = ai_response_data["content"]
            response.parsed_response = parsed_predictions
            response.structured_predictions = [field.to_dict() for field in predicted_fields]
            
            # Calculate metrics
            response.successful_predictions = len(predicted_fields)
            response.overall_confidence = self._calculate_overall_confidence(predicted_fields)
            response.quality_score = response.calculate_quality_score()
            
            # Save everything
            self.db.add(response)
            for field in predicted_fields:
                self.db.add(field)
            
            # Complete the request
            request.complete_processing()
            self.db.commit()
            
            # Log performance metrics
            await self.prediction_logger.log_prediction_metrics(request, response, predicted_fields)
            
            logger.info(f"Completed prediction for request {request.id}: {len(predicted_fields)} fields predicted")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in predict_form_fields for request {request.id}: {str(e)}", exc_info=True)
            
            # Mark request as failed
            error_message = f"Prediction failed: {str(e)}"
            request.fail_processing(error_message, {"exception_type": type(e).__name__})
            
            # Create error response
            if 'response' in locals():
                response.status = ResponseStatus.ERROR.value
                response.has_errors = True
                response.errors = [{"message": error_message, "type": "system_error"}]
                self.db.add(response)
            
            self.db.commit()
            raise
    
    async def _call_ai_model(self, prompt: str, temperature: float = 0.3) -> Dict[str, Any]:
        """Call the AI model with the given prompt."""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant specialized in legal form completion. Provide accurate, helpful predictions while being mindful of legal compliance."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=self.max_tokens
            )
            
            return {
                "content": response.choices[0].message.content,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "model": response.model
            }
            
        except Exception as e:
            logger.error(f"Error calling AI model: {str(e)}", exc_info=True)
            raise
    
    def _extract_predictable_fields(
        self, 
        form_schema: Dict[str, Any], 
        existing_data: Optional[Dict[str, Any]], 
        requested_fields: Optional[List[str]]
    ) -> List[str]:
        """Extract fields that can be predicted."""
        all_fields = []
        
        # Extract from form schema
        if "fields" in form_schema:
            all_fields = [field["name"] for field in form_schema["fields"] if field.get("predictable", True)]
        
        # Filter by requested fields if specified
        if requested_fields:
            all_fields = [field for field in all_fields if field in requested_fields]
        
        # Exclude already filled fields
        if existing_data:
            all_fields = [field for field in all_fields if not existing_data.get(field)]
        
        return all_fields
    
    def _build_prediction_prompt(
        self,
        fields_to_predict: List[str],
        form_schema: Dict[str, Any],
        existing_data: Optional[Dict[str, Any]],
        context_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build the prompt for AI prediction."""
        
        prompt_parts = [
            "Please predict values for the following form fields based on the provided context.",
            "",
            "**Form Information:**"
        ]
        
        # Add form details
        if form_schema.get("title"):
            prompt_parts.append(f"Form: {form_schema['title']}")
        if form_schema.get("description"):
            prompt_parts.append(f"Description: {form_schema['description']}")
        
        prompt_parts.extend([
            "",
            "**Fields to Predict:**"
        ])
        
        # Add field information
        for field_name in fields_to_predict:
            field_info = self._get_field_info(field_name, form_schema)
            prompt_parts.append(f"- {field_name}: {field_info}")
        
        # Add existing data context
        if existing_data:
            prompt_parts.extend([
                "",
                "**Existing Form Data:**",
                json.dumps(existing_data, indent=2)
            ])
        
        # Add user context
        if context_data:
            prompt_parts.extend([
                "",
                "**User Context:**",
                json.dumps(context_data, indent=2)
            ])
        
        prompt_parts.extend([
            "",
            "**Instructions:**",
            "1. Predict reasonable values for each field based on the context",
            "2. Provide a confidence score (0.0-1.0) for each prediction",
            "3. Include reasoning for each prediction",
            "4. Flag any predictions that may require legal review",
            "5. Return predictions in JSON format",
            "",
            "**Response Format:**",
            "```json",
            "{",
            '  "field_name": {',
            '    "predicted_value": "value",',
            '    "confidence": 0.85,',
            '    "reasoning": "explanation",',
            '    "requires_review": false',
            "  }",
            "}",
            "```"
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_field_info(self, field_name: str, form_schema: Dict[str, Any]) -> str:
        """Get field information from schema."""
        if "fields" not in form_schema:
            return "No description available"
        
        for field in form_schema["fields"]:
            if field["name"] == field_name:
                info_parts = []
                if field.get("type"):
                    info_parts.append(f"Type: {field['type']}")
                if field.get("label"):
                    info_parts.append(f"Label: {field['label']}")
                if field.get("description"):
                    info_parts.append(f"Description: {field['description']}")
                if field.get("options"):
                    info_parts.append(f"Options: {', '.join(field['options'])}")
                return " | ".join(info_parts) if info_parts else "No description available"
        
        return "Field not found in schema"
    
    def _parse_ai_response(self, response_content: str) -> Dict[str, Any]:
        """Parse AI response into structured predictions."""
        try:
            # Try to extract JSON from response
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = response_content[json_start:json_end]
                return json.loads(json_content)
            else:
                logger.warning("No JSON found in AI response")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            return {}
    
    async def _create_predicted_field(
        self,
        request: PredictionRequest,
        field_name: str,
        prediction_data: Dict[str, Any],
        form_schema: Dict[str, Any]
    ) -> PredictedField:
        """Create a PredictedField object from prediction data."""
        
        # Extract prediction values
        predicted_value = prediction_data.get("predicted_value", "")
        confidence_score = float(prediction_data.get("confidence", 0.0))
        reasoning = prediction_data.get("reasoning", "")
        requires_review = prediction_data.get("requires_review", False)
        
        # Determine confidence level
        confidence_level = ConfidenceLevel.LOW
        if confidence_score >= 0.9:
            confidence_level = ConfidenceLevel.HIGH
        elif confidence_score >= 0.7:
            confidence_level = ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.5:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.VERY_LOW
        
        # Get field information
        field_info = self._get_field_schema(field_name, form_schema)
        
        # Create predicted field
        predicted_field = PredictedField(
            prediction_request_id=request.id,
            form_id=request.form_id,
            document_id=request.document_id,
            user_id=request.user_id,
            field_name=field_name,
            field_type=field_info.get("type", "text"),
            field_category=field_info.get("category", "general"),
            field_label=field_info.get("label"),
            predicted_value=str(predicted_value) if predicted_value is not None else None,
            confidence_score=confidence_score,
            confidence_level=confidence_level.value,
            reasoning=reasoning,
            model_used=self.model_name,
            model_version="1.0",
            requires_review=requires_review,
            jurisdiction=request.jurisdiction
        )
        
        # Apply UPL safeguards
        predicted_field.apply_upv_safeguards(field_info)
        
        # Validate the prediction
        await self._validate_predicted_field(predicted_field, field_info)
        
        return predicted_field
    
    def _get_field_schema(self, field_name: str, form_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Get field schema information."""
        if "fields" not in form_schema:
            return {}
        
        for field in form_schema["fields"]:
            if field["name"] == field_name:
                return field
        
        return {}
    
    async def _validate_predicted_field(self, predicted_field: PredictedField, field_schema: Dict[str, Any]):
        """Validate a predicted field value."""
        validation_errors = []
        
        # Type validation
        field_type = field_schema.get("type", "text")
        if field_type == "email" and predicted_field.predicted_value:
            if "@" not in predicted_field.predicted_value:
                validation_errors.append("Invalid email format")
        
        elif field_type == "phone" and predicted_field.predicted_value:
            # Basic phone validation
            cleaned_phone = ''.join(filter(str.isdigit, predicted_field.predicted_value))
            if len(cleaned_phone) < 10:
                validation_errors.append("Phone number too short")
        
        elif field_type == "date" and predicted_field.predicted_value:
            try:
                datetime.fromisoformat(predicted_field.predicted_value.replace('Z', '+00:00'))
            except ValueError:
                validation_errors.append("Invalid date format")
        
        # Required field validation
        if field_schema.get("required", False) and not predicted_field.predicted_value:
            validation_errors.append("Required field cannot be empty")
        
        # Options validation
        if field_schema.get("options") and predicted_field.predicted_value:
            if predicted_field.predicted_value not in field_schema["options"]:
                validation_errors.append(f"Value must be one of: {', '.join(field_schema['options'])}")
        
        # Update validation results
        predicted_field.is_valid = len(validation_errors) == 0
        if validation_errors:
            predicted_field.validation_errors = validation_errors
    
    def _calculate_overall_confidence(self, predicted_fields: List[PredictedField]) -> float:
        """Calculate overall confidence across all predicted fields."""
        if not predicted_fields:
            return 0.0
        
        confidence_scores = [field.confidence_score for field in predicted_fields]
        return sum(confidence_scores) / len(confidence_scores)
    
    async def retry_failed_predictions(self, request_id: int) -> PredictionResponse:
        """Retry failed predictions for a request."""
        request = self.db.query(PredictionRequest).filter(PredictionRequest.id == request_id).first()
        
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        if not request.can_retry:
            raise ValueError(f"Request {request_id} cannot be retried")
        
        # Prepare for retry
        request.retry_request()
        self.db.commit()
        
        # Re-run prediction
        return await self.predict_form_fields(
            request, 
            request.form_schema,
            request.existing_data,
            request.context_data
        )
    
    async def get_prediction_status(self, request_id: int) -> Dict[str, Any]:
        """Get status of a prediction request."""
        request = self.db.query(PredictionRequest).filter(PredictionRequest.id == request_id).first()
        
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        predicted_fields = self.db.query(PredictedField).filter(
            PredictedField.prediction_request_id == request_id
        ).all()
        
        return {
            "request_id": request_id,
            "status": request.status,
            "total_fields": len(predicted_fields),
            "high_confidence": len([f for f in predicted_fields if f.confidence_score >= 0.9]),
            "medium_confidence": len([f for f in predicted_fields if 0.7 <= f.confidence_score < 0.9]),
            "low_confidence": len([f for f in predicted_fields if f.confidence_score < 0.7]),
            "requires_review": len([f for f in predicted_fields if f.requires_review]),
            "average_confidence": request.average_confidence,
            "processing_time_ms": request.processing_time_ms,
            "completed_at": request.completed_at.isoformat() if request.completed_at else None
        }
