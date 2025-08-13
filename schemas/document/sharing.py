from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class AccessLevel(str, Enum):
	VIEW = "view"


class ShareType(str, Enum):
	LINK = "link"


class ShareStatus(str, Enum):
	ACTIVE = "active"


class LinkAccess(str, Enum):
	ANYONE = "anyone"


class DocumentShareCreate(BaseModel):
	document_id: Optional[int] = None


class DocumentShareUpdate(BaseModel):
	pass


class DocumentShareResponse(BaseModel):
	id: int


class ShareLinkAccessRequest(BaseModel):
	pass


class DocumentPermissionCheck(BaseModel):
	can_read: bool = True
	can_update: bool = True
	can_correct: bool = True
	can_predict: bool = True


class DocumentPermissionResponse(DocumentPermissionCheck):
	pass


class ShareListParams(BaseModel):
	limit: int = 50


class ShareStats(BaseModel):
	total: int = 0


class BulkShareAction(BaseModel):
	action: str


