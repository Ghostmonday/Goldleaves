from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class VersionComparisonRequest(BaseModel):
	from_version: int
	to_version: int
	include_content_diff: bool = True
	include_metadata_diff: bool = True
	diff_format: Optional[str] = None


class SecureShareCreate(BaseModel):
	recipient_email: Optional[str] = None
	recipient_name: Optional[str] = None
	permission_level: Optional[str] = None
	expires_at: Optional[datetime] = None
	allowed_views: Optional[int] = 0
	allowed_downloads: Optional[int] = 0
	requires_authentication: Optional[bool] = False
	track_access: Optional[bool] = True
	requires_access_code: Optional[bool] = False
	share_reason: Optional[str] = None


class ShareAccessRequest(BaseModel):
	access_code: Optional[str] = None


