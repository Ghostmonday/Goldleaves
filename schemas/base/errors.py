"""Minimal error schema stubs for tests."""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel


class ErrorCode(str, Enum):
	UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
	INFO = "info"
	WARN = "warn"
	ERROR = "error"


class FieldError(BaseModel):
	field: str
	message: str


class ErrorDetail(BaseModel):
	code: ErrorCode = ErrorCode.UNKNOWN
	message: str = ""


class ValidationError(BaseModel):
	detail: str | None = None


class BusinessError(BaseModel):
	detail: str | None = None


class SystemError(BaseModel):
	detail: str | None = None


class RateLimitError(BaseModel):
	detail: str | None = None


def create_validation_error(*args, **kwargs) -> ValidationError:
	return ValidationError(detail=kwargs.get("detail"))


def create_field_error(*args, **kwargs) -> FieldError:
	return FieldError(field=kwargs.get("field", ""), message=kwargs.get("message", ""))


def create_business_error(*args, **kwargs) -> BusinessError:
	return BusinessError(detail=kwargs.get("detail"))


def create_system_error(*args, **kwargs) -> SystemError:
	return SystemError(detail=kwargs.get("detail"))


def create_rate_limit_error(*args, **kwargs) -> RateLimitError:
	return RateLimitError(detail=kwargs.get("detail"))

# For compatibility with schemas.base.__init__ expecting ErrorResponse from errors
class ErrorResponse(BaseModel):
	message: str | None = None
	error: str | None = None


