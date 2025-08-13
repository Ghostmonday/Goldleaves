from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BulkAction(str):
	pass


class BulkDocumentRequest(BaseModel):
	document_ids: List[int]


class BulkOperationResponse(BaseModel):
	success_count: int = 0
	error_count: int = 0
	updated_documents: List[int] = Field(default_factory=list)


class BulkMoveRequest(BaseModel):
	pass


class BulkCopyRequest(BaseModel):
	pass


class BulkMetadataUpdate(BaseModel):
	pass


class BulkPermissionRequest(BaseModel):
	pass


class BulkTagRequest(BaseModel):
	pass


class BulkOperationResult(BaseModel):
	pass


class BulkOperationStats(BaseModel):
	pass


class BulkOperationListParams(BaseModel):
	limit: int = 50


class BulkExportRequest(BaseModel):
	pass


class BulkUpdateMetadataRequest(BaseModel):
	pass


class BulkOperationStatus(BaseModel):
	status: str = "completed"


class BulkOperationCancel(BaseModel):
	pass


class BulkListParams(BaseModel):
	limit: int = 50


class BulkStatusCheck(BaseModel):
	status: str = "ok"


