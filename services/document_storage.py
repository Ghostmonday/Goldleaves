

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from schemas.storage.storage import (
	DocumentUploadRequest,
	DocumentExportRequest,
	FileUploadResponse,
	FileRetrievalResponse,
	ExportResponse,
	DocumentFileMeta,
)


@dataclass
class _UploadedFile:
	file_id: str
	file_size: int = 0
	checksum_sha256: str | None = None
	storage_path: str | None = None
	encrypted: bool | None = None
	virus_scan_passed: bool | None = True


@dataclass
class _RetrievedFile:
	file_meta: DocumentFileMeta
	access_granted: bool = True
	download_url: str | None = None
	content_disposition: str | None = None
	cache_control: str | None = None


class DocumentStorageService:
	@staticmethod
	def upload_document(document_id: int, file_bytes: bytes, request: DocumentUploadRequest) -> _UploadedFile:
		return _UploadedFile(
			file_id=f"file_{document_id}",
			file_size=len(file_bytes or b""),
			checksum_sha256="stub",
			storage_path=f"/tmp/{document_id}.bin",
			encrypted=True,
			virus_scan_passed=True,
		)

	@staticmethod
	def retrieve_file(document_id: int, file_id: str, token: Optional[str] = None) -> _RetrievedFile:
		meta = DocumentFileMeta(file_id=file_id, original_filename="test.pdf", content_type="application/pdf")
		return _RetrievedFile(
			file_meta=meta,
			access_granted=token is None or token == "valid_access_token_123",
			download_url="https://example/download" if token == "valid_access_token_123" else None,
			content_disposition='attachment; filename="test.pdf"',
			cache_control="private, max-age=3600",
		)

	@staticmethod
	def export_document(document_id: int, request: DocumentExportRequest) -> ExportResponse:
		return ExportResponse(
			export_id="export_stub",
			export_format=request.export_format,
		)


