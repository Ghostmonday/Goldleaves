"""Schemas for form tests (minimal)."""
from __future__ import annotations
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional
from models.forms import FormType

class JurisdictionInfo(BaseModel):
    state: str
    county: Optional[str] = None
    court_type: Optional[str] = None

    @validator("state")
    def validate_state(cls, v):
        if len(v) != 2:
            raise ValueError("Invalid state code")
        return v

class FormMetadata(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    jurisdiction: JurisdictionInfo
    form_number: Optional[str] = None
    language: str = "en"

class FormUploadRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    title: str
    description: Optional[str] = None
    form_type: FormType
    metadata: FormMetadata
    tags: List[str] = Field(default_factory=list)


