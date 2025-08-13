from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class FileFormat(str, Enum):
	PDF = "pdf"
	DOCX = "docx"
	TXT = "txt"


class ExportFormat(str, Enum):
	PDF_ANNOTATED = "pdf_annotated"
	JSON_STRUCTURED = "json_structured"
	ARCHIVE_BUNDLE = "archive_bundle"
	PDF_CLEAN = "pdf_clean"


class EncryptionType(str, Enum):
	AES256 = "aes256"


class DocumentUploadRequest(BaseModel):
	is_primary_file: Optional[bool] = None
	upload_reason: Optional[str] = None


class DocumentExportRequest(BaseModel):
	export_format: ExportFormat
	include_version_history: bool | None = None
	include_audit_trail: bool | None = None
	include_collaboration_data: bool | None = None
	include_ai_annotations: bool | None = None
	watermark_config: dict | None = None
	lineage_preservation_level: Optional[str] = None
	ada_compliance_level: Optional[str] = None


class FileUploadResponse(BaseModel):
	file_id: str


class FileRetrievalResponse(BaseModel):
	access_granted: bool


class ExportResponse(BaseModel):
	export_id: str
	export_format: ExportFormat


class DocumentFileMeta(BaseModel):
	file_id: str
	original_filename: Optional[str] = None
	file_size: Optional[int] = None
	content_type: Optional[str] = None
	storage_path: Optional[str] = None
	checksum_sha256: Optional[str] = None
	encrypted: Optional[bool] = None


class StorageStats(BaseModel):
	total_files: int = 0


class ExportMetadata(BaseModel):
	export_id: str
	created_at: datetime | None = None
	entries: list[str] | None = None


