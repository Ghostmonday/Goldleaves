from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
	title: str
	document_type: str | Enum | None = None
	status: str | None = None
	confidentiality: str | None = None
	case_id: Optional[int] = None
	client_id: Optional[int] = None
	content: Optional[str] = None
	ai_predictions: Optional[Dict[str, Any]] = None
	prediction_score: Optional[float] = None
	prediction_status: Optional[str] = None
	tags: List[str] = Field(default_factory=list)


class DocumentUpdate(BaseModel):
	title: Optional[str] = None
	status: Optional[str] = None
	confidentiality: Optional[str] = None
	content: Optional[str] = None


class DocumentFilter(BaseModel):
	min_prediction_score: Optional[float] = None
	prediction_status: Optional[str] = None
	tags: Optional[List[str]] = None


class DocumentResponse(BaseModel):
	id: int
	title: str
	document_type: str


class DocumentStats(BaseModel):
	total_count: int = 0


class DocumentPermissionCheck(BaseModel):
	can_read: bool = True
	can_update: bool = True
	can_correct: bool = True
	can_predict: bool = True


class DocumentSearchResponse(BaseModel):
	items: List[DocumentResponse] = Field(default_factory=list)
	total: int = 0


