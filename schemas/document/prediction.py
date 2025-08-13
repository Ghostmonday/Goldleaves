from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class PredictionField(BaseModel):
	field_name: str
	predicted_value: Any
	confidence: float
	field_type: Optional[str] = None
	alternatives: Optional[List[Any]] = None
	original_text: Optional[str] = None


class DocumentPrediction(BaseModel):
	model_name: str
	model_version: str
	prediction_timestamp: datetime
	overall_confidence: float
	predictions: List[PredictionField]
	document_classification: Optional[str] = None
	entities: Optional[List[str]] = None
	key_phrases: Optional[List[str]] = None
	risk_indicators: Optional[List[str]] = None


class PredictionIngest(BaseModel):
	prediction_data: DocumentPrediction
	auto_apply_high_confidence: bool = False
	validation_required: bool = False


