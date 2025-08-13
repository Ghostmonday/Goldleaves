

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class CommentType(str, Enum):
	GENERAL = "general"


class CommentStatus(str, Enum):
	OPEN = "open"
	RESOLVED = "resolved"


class CommentReaction(str, Enum):
	LIKE = "like"


class CommentAnchor(BaseModel):
	path: str
	start: int | None = None
	end: int | None = None


class CommentCreate(BaseModel):
	text: str


class CommentUpdate(BaseModel):
	text: Optional[str] = None
	status: Optional[CommentStatus] = None


class CommentResponse(BaseModel):
	id: str
	text: str
	status: CommentStatus = CommentStatus.OPEN


class CommentThread(BaseModel):
	id: str


class CommentListParams(BaseModel):
	page: int = 1
	size: int = 20


class CommentReactionRequest(BaseModel):
	reaction: CommentReaction


class CommentModerationRequest(BaseModel):
	action: str


class CommentStats(BaseModel):
	total: int = 0


class BulkCommentAction(str, Enum):
	DELETE = "delete"


