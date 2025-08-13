

from __future__ import annotations

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from .pagination import PaginatedResponse  # re-export to satisfy imports in schemas.case.core


class BaseResponse(BaseModel):
	message: str | None = None
	data: Any | None = None


class SuccessResponse(BaseResponse):
	success: bool = True


class ErrorResponse(BaseResponse):
	success: bool = False
	error: str | None = None


class ValidationErrorResponse(ErrorResponse):
	errors: List[dict] | None = None


class NotFoundResponse(ErrorResponse):
	status_code: int = 404


class UnauthorizedResponse(ErrorResponse):
	status_code: int = 401


class ForbiddenResponse(ErrorResponse):
	status_code: int = 403


class ConflictResponse(ErrorResponse):
	status_code: int = 409


class RateLimitResponse(ErrorResponse):
	status_code: int = 429


class ServerErrorResponse(ErrorResponse):
	status_code: int = 500


def create_success_response(message: str = "ok", data: Any | None = None) -> SuccessResponse:
	return SuccessResponse(message=message, data=data)


def create_error_response(message: str = "error", error: str | None = None, data: Any | None = None) -> ErrorResponse:
	return ErrorResponse(message=message, error=error, data=data)


def create_validation_error_response(errors: List[dict] | None = None, message: str = "validation_error") -> ValidationErrorResponse:
	return ValidationErrorResponse(message=message, error="validation_error", errors=errors)


def create_not_found_response(message: str = "not_found") -> NotFoundResponse:
	return NotFoundResponse(message=message, error="not_found")


