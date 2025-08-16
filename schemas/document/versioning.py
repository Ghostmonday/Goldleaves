from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel

from enum import Enum


class VersionType(str, Enum):
	MAJOR = "major"
	MINOR = "minor"


class VersionStatus(str, Enum):
	ACTIVE = "active"
	ARCHIVED = "archived"


class ChangeType(str, Enum):
	ADDED = "added"
	MODIFIED = "modified"
	REMOVED = "removed"


class MergeConflictType(str, Enum):
	FIELD = "field"
	CONTENT = "content"


class MergeConflict(BaseModel):
	conflict_type: MergeConflictType
	field_name: Optional[str] = None
	description: Optional[str] = None


class VersionComparisonRequest(BaseModel):
	from_version: int
	to_version: int
	include_content_diff: bool = True
	include_metadata_diff: bool = True
	diff_format: str | None = None


class VersionDiff(BaseModel):
	document_id: int
	from_version: int
	to_version: int
	total_changes: int
	field_diffs: List[dict] = []
	content_diff: Optional[str] = None
	diff_summary: Optional[str] = None


class VersionComparisonResponse(VersionDiff):
	pass


class DocumentVersionCreate(BaseModel):
	version_number: int


class DocumentVersionUpdate(BaseModel):
	version_number: int


class DocumentVersionResponse(BaseModel):
	id: int
	version_number: int


class VersionListParams(BaseModel):
	limit: int = 50


class VersionStats(BaseModel):
	total_versions: int = 0


class VersionMergeRequest(BaseModel):
	target_version: int


class VersionRestoreRequest(BaseModel):
	target_version: int


class BulkVersionAction(BaseModel):
	action: str


