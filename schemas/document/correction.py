# schemas/document/correction.py

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class CorrectionType(str, Enum):
    """Types of corrections that can be made."""
    CONFIRM = "confirm"
    REJECT = "reject"
    MODIFY = "modify"
    ADD_FIELD = "add_field"
    REMOVE_FIELD = "remove_field"


class FieldCorrection(BaseModel):
    """Individual field correction details."""
    field_path: str = Field(..., description="JSON path to the field being corrected")
    correction_type: CorrectionType = Field(..., description="Type of correction")
    original_value: Any = Field(None, description="Original AI predicted value")
    corrected_value: Any = Field(None, description="Human-corrected value")
    confidence_before: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence before correction")
    confidence_after: float = Field(1.0, ge=0.0, le=1.0, description="Human confidence after correction")
    source_evidence: Optional[str] = Field(None, description="Evidence supporting the correction")
    
    @validator('corrected_value')
    def validate_corrected_value_for_modify(cls, v, values):
        """Ensure corrected value is provided for modify corrections."""
        if values.get('correction_type') == CorrectionType.MODIFY and v is None:
            raise ValueError("Corrected value is required for modify corrections")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "field_path": "contract_value",
                "correction_type": "modify",
                "original_value": 250000.00,
                "corrected_value": 275000.00,
                "confidence_before": 0.85,
                "confidence_after": 1.0,
                "source_evidence": "Verified against signed contract addendum"
            }
        }


class DocumentCorrection(BaseModel):
    """Schema for creating document corrections."""
    corrections: List[FieldCorrection] = Field(..., description="List of field corrections")
    correction_reason: str = Field(..., description="Overall reason for corrections")
    reviewer_notes: Optional[str] = Field(None, description="Additional reviewer notes")
    requires_review: bool = Field(False, description="Whether correction requires additional review")
    
    @validator('corrections')
    def validate_corrections_not_empty(cls, v):
        """Ensure at least one correction is provided."""
        if not v:
            raise ValueError("At least one correction is required")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "corrections": [
                    {
                        "field_path": "contract_value",
                        "correction_type": "modify",
                        "original_value": 250000.00,
                        "corrected_value": 275000.00,
                        "confidence_before": 0.85
                    },
                    {
                        "field_path": "payment_terms",
                        "correction_type": "add_field",
                        "corrected_value": "Net 30 days"
                    }
                ],
                "correction_reason": "Updated values from contract amendment",
                "reviewer_notes": "Client requested changes documented in Amendment #2",
                "requires_review": True
            }
        }


class CorrectionCreate(BaseModel):
    """Schema for creating a new correction record."""
    field_path: str = Field(..., description="JSON path to corrected field")
    original_value: Any = Field(None, description="Original AI prediction")
    corrected_value: Any = Field(None, description="Human-corrected value")
    confidence_before: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_after: float = Field(1.0, ge=0.0, le=1.0)
    correction_reason: str = Field(..., description="Reason for correction")
    correction_type: str = Field(..., description="Type of correction")
    
    class Config:
        schema_extra = {
            "example": {
                "field_path": "contract_value",
                "original_value": 250000.00,
                "corrected_value": 275000.00,
                "confidence_before": 0.85,
                "confidence_after": 1.0,
                "correction_reason": "Contract amendment increased value",
                "correction_type": "modify"
            }
        }


class CorrectionUpdate(BaseModel):
    """Schema for updating an existing correction."""
    corrected_value: Optional[Any] = Field(None, description="Updated corrected value")
    confidence_after: Optional[float] = Field(None, ge=0.0, le=1.0)
    correction_reason: Optional[str] = Field(None, description="Updated reason")
    review_status: Optional[str] = Field(None, description="Review status")
    
    class Config:
        schema_extra = {
            "example": {
                "corrected_value": 280000.00,
                "confidence_after": 0.95,
                "correction_reason": "Further updated per legal team review",
                "review_status": "approved"
            }
        }


class CorrectionResponse(BaseModel):
    """Schema for correction response data."""
    id: int
    document_id: int
    field_path: str
    original_value: Any
    corrected_value: Any
    confidence_before: Optional[float]
    confidence_after: float
    correction_reason: str
    correction_type: str
    
    # User and review information
    corrected_by_id: int
    corrected_by_name: Optional[str] = Field(None, description="Name of user who made correction")
    reviewed_by_id: Optional[int]
    reviewed_by_name: Optional[str] = Field(None, description="Name of user who reviewed")
    reviewed_at: Optional[datetime]
    review_status: str
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "document_id": 1,
                "field_path": "contract_value",
                "original_value": 250000.00,
                "corrected_value": 275000.00,
                "confidence_before": 0.85,
                "confidence_after": 1.0,
                "correction_reason": "Contract amendment increased value",
                "correction_type": "modify",
                "corrected_by_id": 1,
                "corrected_by_name": "John Attorney",
                "review_status": "approved",
                "created_at": "2025-08-02T10:30:00Z"
            }
        }


class CorrectionValidation(BaseModel):
    """Schema for validating corrections before applying."""
    field_path: str
    proposed_value: Any
    validation_rules: List[str] = Field(default_factory=list, description="Validation rules to check")
    
    class Config:
        schema_extra = {
            "example": {
                "field_path": "contract_value",
                "proposed_value": 275000.00,
                "validation_rules": ["positive_number", "currency_format", "reasonable_range"]
            }
        }


class CorrectionValidationResult(BaseModel):
    """Result of correction validation."""
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    suggested_value: Optional[Any] = Field(None, description="System-suggested value if applicable")
    
    class Config:
        schema_extra = {
            "example": {
                "is_valid": True,
                "validation_errors": [],
                "validation_warnings": ["Value is 10% higher than similar contracts"],
                "suggested_value": None
            }
        }


class CorrectionBatch(BaseModel):
    """Schema for batch correction operations."""
    document_ids: List[int] = Field(..., description="Documents to apply corrections to")
    corrections: List[FieldCorrection] = Field(..., description="Corrections to apply")
    apply_to_similar: bool = Field(False, description="Apply to similar documents")
    similarity_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Similarity threshold for auto-apply")
    
    class Config:
        schema_extra = {
            "example": {
                "document_ids": [1, 2, 3],
                "corrections": [
                    {
                        "field_path": "contract_value",
                        "correction_type": "modify",
                        "corrected_value": 275000.00
                    }
                ],
                "apply_to_similar": True,
                "similarity_threshold": 0.85
            }
        }


class CorrectionBatchResult(BaseModel):
    """Result of batch correction operations."""
    total_documents: int
    successful_corrections: int
    failed_corrections: int
    correction_results: List[Dict[str, Any]] = Field(default_factory=list)
    similar_documents_found: int = 0
    similar_documents_updated: int = 0
    
    class Config:
        schema_extra = {
            "example": {
                "total_documents": 3,
                "successful_corrections": 2,
                "failed_corrections": 1,
                "correction_results": [
                    {"document_id": 1, "success": True, "corrections_applied": 1},
                    {"document_id": 2, "success": True, "corrections_applied": 1},
                    {"document_id": 3, "success": False, "error": "Document locked"}
                ],
                "similar_documents_found": 5,
                "similar_documents_updated": 4
            }
        }
