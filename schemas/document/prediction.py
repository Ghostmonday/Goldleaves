# schemas/document/prediction.py

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

from models.document import PredictionStatus


class PredictionField(BaseModel):
    """Individual prediction field with confidence score."""
    field_name: str = Field(..., description="Name of the predicted field")
    predicted_value: Any = Field(..., description="AI predicted value")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this field")
    source_text: Optional[str] = Field(None, description="Source text that led to this prediction")
    extraction_method: Optional[str] = Field(None, description="Method used for extraction (OCR, NLP, etc.)")
    
    class Config:
        schema_extra = {
            "example": {
                "field_name": "contract_value",
                "predicted_value": 250000.00,
                "confidence_score": 0.92,
                "source_text": "Total contract value: $250,000.00",
                "extraction_method": "regex_currency"
            }
        }


class DocumentPrediction(BaseModel):
    """Complete AI prediction payload for a document."""
    model_name: str = Field(..., description="Name/version of AI model used")
    model_version: str = Field(..., description="Version of the AI model")
    prediction_timestamp: datetime = Field(..., description="When prediction was made")
    
    # Overall prediction metadata
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall prediction confidence")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    
    # Individual field predictions
    predictions: List[PredictionField] = Field(..., description="Individual field predictions")
    
    # Document classification
    document_classification: Optional[Dict[str, float]] = Field(
        None, 
        description="Document type classification with confidence scores"
    )
    
    # Extracted entities
    entities: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Named entities extracted from document"
    )
    
    # Key phrases and topics
    key_phrases: Optional[List[str]] = Field(None, description="Key phrases identified")
    topics: Optional[List[Dict[str, float]]] = Field(None, description="Topics with confidence scores")
    
    # Compliance and risk indicators
    risk_indicators: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Potential compliance or legal risk indicators"
    )
    
    @validator('predictions')
    def validate_predictions_not_empty(cls, v):
        """Ensure at least one prediction is provided."""
        if not v:
            raise ValueError("At least one field prediction is required")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "model_name": "LegalDocAI",
                "model_version": "v2.1.0",
                "prediction_timestamp": "2025-08-02T10:30:00Z",
                "overall_confidence": 0.89,
                "processing_time_ms": 1250,
                "predictions": [
                    {
                        "field_name": "contract_value",
                        "predicted_value": 250000.00,
                        "confidence_score": 0.92,
                        "source_text": "Total contract value: $250,000.00"
                    },
                    {
                        "field_name": "effective_date",
                        "predicted_value": "2025-01-01",
                        "confidence_score": 0.87,
                        "source_text": "Effective January 1, 2025"
                    }
                ],
                "document_classification": {
                    "contract": 0.95,
                    "legal_brief": 0.03,
                    "correspondence": 0.02
                },
                "entities": [
                    {"type": "ORGANIZATION", "text": "Acme Corporation", "confidence": 0.98},
                    {"type": "MONEY", "text": "$250,000.00", "confidence": 0.95}
                ],
                "key_phrases": ["service agreement", "contract terms", "payment schedule"],
                "risk_indicators": [
                    {
                        "type": "liability_cap",
                        "description": "No liability cap found",
                        "severity": "medium"
                    }
                ]
            }
        }


class PredictionIngest(BaseModel):
    """Schema for ingesting AI predictions into a document."""
    prediction_data: DocumentPrediction = Field(..., description="Complete prediction payload")
    auto_apply_high_confidence: bool = Field(
        False, 
        description="Automatically apply predictions with confidence >= 0.95"
    )
    notify_reviewers: bool = Field(True, description="Notify human reviewers of new predictions")
    
    class Config:
        schema_extra = {
            "example": {
                "prediction_data": {
                    "model_name": "LegalDocAI",
                    "model_version": "v2.1.0",
                    "overall_confidence": 0.89,
                    "predictions": [
                        {
                            "field_name": "contract_value",
                            "predicted_value": 250000.00,
                            "confidence_score": 0.92
                        }
                    ]
                },
                "auto_apply_high_confidence": True,
                "notify_reviewers": True
            }
        }


class PredictionConfirm(BaseModel):
    """Schema for confirming AI predictions."""
    field_paths: List[str] = Field(..., description="JSON paths of fields to confirm")
    confirmation_reason: Optional[str] = Field(None, description="Reason for confirmation")
    reviewer_notes: Optional[str] = Field(None, description="Additional reviewer notes")
    
    class Config:
        schema_extra = {
            "example": {
                "field_paths": ["contract_value", "effective_date"],
                "confirmation_reason": "Verified against original document",
                "reviewer_notes": "All monetary values cross-checked with accounting"
            }
        }


class PredictionReject(BaseModel):
    """Schema for rejecting AI predictions."""
    field_paths: List[str] = Field(..., description="JSON paths of fields to reject")
    rejection_reason: str = Field(..., description="Reason for rejection")
    correct_values: Optional[Dict[str, Any]] = Field(
        None, 
        description="Correct values if known"
    )
    reviewer_notes: Optional[str] = Field(None, description="Additional reviewer notes")
    
    class Config:
        schema_extra = {
            "example": {
                "field_paths": ["contract_value"],
                "rejection_reason": "Incorrect currency conversion",
                "correct_values": {
                    "contract_value": 275000.00
                },
                "reviewer_notes": "Amount should be in USD, not EUR"
            }
        }


class PredictionBatch(BaseModel):
    """Schema for batch prediction operations."""
    document_ids: List[int] = Field(..., description="Documents to process")
    ml_model_config: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Model configuration parameters"
    )
    priority: str = Field("normal", description="Processing priority: low, normal, high")
    callback_url: Optional[str] = Field(None, description="Webhook URL for completion notification")
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority level."""
        if v not in ["low", "normal", "high"]:
            raise ValueError("Priority must be 'low', 'normal', or 'high'")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "document_ids": [1, 2, 3, 4, 5],
                "ml_model_config": {
                    "confidence_threshold": 0.7,
                    "enable_classification": True,
                    "extract_entities": True
                },
                "priority": "high",
                "callback_url": "https://api.example.com/webhooks/predictions"
            }
        }


class PredictionResult(BaseModel):
    """Result of prediction processing."""
    document_id: int
    success: bool
    prediction_status: PredictionStatus
    confidence_score: Optional[float]
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": 1,
                "success": True,
                "prediction_status": "pending",
                "confidence_score": 0.89,
                "processing_time_ms": 1250
            }
        }


class PredictionBatchResult(BaseModel):
    """Result of batch prediction processing."""
    batch_id: str = Field(..., description="Unique batch identifier")
    total_documents: int
    successful_predictions: int
    failed_predictions: int
    results: List[PredictionResult]
    
    # Timing information
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_processing_time_ms: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_2025080210_abc123",
                "total_documents": 5,
                "successful_predictions": 4,
                "failed_predictions": 1,
                "results": [
                    {
                        "document_id": 1,
                        "success": True,
                        "prediction_status": "pending",
                        "confidence_score": 0.89
                    }
                ],
                "started_at": "2025-08-02T10:30:00Z",
                "completed_at": "2025-08-02T10:32:15Z",
                "total_processing_time_ms": 135000
            }
        }
