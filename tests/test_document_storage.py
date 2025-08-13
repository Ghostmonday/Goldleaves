# tests/test_document_storage.py

"""Comprehensive tests for Phase 7: Document storage, export, and court packaging."""

import os
import json
import tempfile
import zipfile
from io import BytesIO
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models.user import User
from models.document import Document
from models.contract import Contract, ContractStatus
from schemas.storage.storage import (
    DocumentUploadRequest, DocumentExportRequest, FileFormat,
    EncryptionType, ExportFormat
)
from schemas.storage.court_packaging import (
    CourtPackagingRequest, JurisdictionType, PackagingFlags,
    AttorneyInfo, CaseInfo
)
from services.document_storage import DocumentStorageService
from core.exceptions import NotFoundError, ValidationError, PermissionError

client = TestClient(app)


class TestDocumentUpload:
    """Test document file upload functionality."""

    def test_upload_valid_pdf_file(self, db: Session, test_user: User, test_contract: Contract):
        """Test uploading a valid PDF file."""
        # Create test document
        document = Document(
            contract_id=test_contract.id,
            title="Test Document",
            organization_id=test_user.organization_id,
            created_by_id=test_user.id
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Create test PDF content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj"

        with patch('services.document_storage.DocumentStorageService.upload_document') as mock_upload:
            mock_upload.return_value = MagicMock(
                file_id="file_123",
                file_size=len(pdf_content),
                checksum_sha256="abc123",
                storage_path="/test/path/file_123.pdf",
                encrypted=True,
                virus_scan_passed=True
            )

            response = client.post(
                f"/documents/{document.id}/upload",
                files={"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")},
                params={
                    "is_primary_file": True,
                    "upload_reason": "Initial document upload",
                    "tags": ["contract", "signed"]
                },
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == "file_123"
        assert data["virus_scan_passed"] is True
        assert data["encrypted"] is True

    def test_upload_oversized_file_rejection(self, db: Session, test_user: User, test_contract: Contract):
        """Test rejection of oversized files."""
        document = Document(
            contract_id=test_contract.id,
            title="Test Document",
            organization_id=test_user.organization_id,
            created_by_id=test_user.id
        )
        db.add(document)
        db.commit()

        # Create oversized content (simulate 101MB file)
        large_content = b"x" * (101 * 1024 * 1024)

        response = client.post(
            f"/documents/{document.id}/upload",
            files={"file": ("large.pdf", BytesIO(large_content), "application/pdf")},
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        assert response.status_code == 400
        assert "exceeds maximum limit" in response.json()["detail"]

    def test_upload_unsupported_file_format(self, db: Session, test_user: User, test_contract: Contract):
        """Test rejection of unsupported file formats."""
        document = Document(
            contract_id=test_contract.id,
            title="Test Document",
            organization_id=test_user.organization_id,
            created_by_id=test_user.id
        )
        db.add(document)
        db.commit()

        # Try to upload unsupported format
        response = client.post(
            f"/documents/{document.id}/upload",
            files={"file": ("test.exe", BytesIO(b"executable content"), "application/x-executable")},
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]

    def test_upload_unauthorized_access(self, db: Session, test_contract: Contract):
        """Test upload rejection for unauthorized users."""
        document = Document(
            contract_id=test_contract.id,
            title="Test Document",
            organization_id=999,  # Different organization
            created_by_id=999
        )
        db.add(document)
        db.commit()

        response = client.post(
            f"/documents/{document.id}/upload",
            files={"file": ("test.pdf", BytesIO(b"content"), "application/pdf")},
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    @patch('services.document_storage.DocumentStorageService._scan_file_for_viruses')
    def test_upload_virus_detection(self, mock_virus_scan, db: Session, test_user: User, test_contract: Contract):
        """Test virus detection during upload."""
        mock_virus_scan.return_value = (False, "Virus detected: Eicar-Test-Signature")

        document = Document(
            contract_id=test_contract.id,
            title="Test Document",
            organization_id=test_user.organization_id,
            created_by_id=test_user.id
        )
        db.add(document)
        db.commit()

        response = client.post(
            f"/documents/{document.id}/upload",
            files={"file": ("malicious.pdf", BytesIO(b"EICAR test virus"), "application/pdf")},
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        assert response.status_code == 400
        assert "virus" in response.json()["detail"].lower()


class TestDocumentDownload:
    """Test document file download functionality."""

    def test_get_file_info_success(self, db: Session, test_user: User, test_document_with_file):
        """Test successful file info retrieval."""
        document, file_meta = test_document_with_file

        with patch('services.document_storage.DocumentStorageService.retrieve_file') as mock_retrieve:
            mock_retrieve.return_value = MagicMock(
                file_meta=file_meta,
                access_granted=True,
                download_url="https://storage.example.com/download/token123",
                content_disposition='attachment; filename="test.pdf"',
                cache_control="private, max-age=3600"
            )

            response = client.get(
                f"/documents/{document.id}/download",
                params={"include_download_url": True},
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert "download_url" in data

    def test_download_file_with_valid_token(self, db: Session, test_user: User, test_document_with_file):
        """Test file download with valid access token."""
        document, file_meta = test_document_with_file

        # Create temporary test file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(b"Test PDF content")
            temp_file_path = temp_file.name

        with patch('services.document_storage.DocumentStorageService.retrieve_file') as mock_retrieve:
            mock_retrieve.return_value = MagicMock(
                file_meta=MagicMock(
                    storage_path=temp_file_path,
                    original_filename="test.pdf",
                    content_type="application/pdf"
                ),
                access_granted=True,
                content_disposition='attachment; filename="test.pdf"',
                cache_control="private, max-age=3600"
            )

            response = client.get(
                f"/documents/{document.id}/files/{file_meta.file_id}/download",
                params={"token": "valid_access_token_123"},
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

        # Cleanup
        os.unlink(temp_file_path)

    def test_download_with_invalid_token(self, db: Session, test_user: User, test_document_with_file):
        """Test download rejection with invalid token."""
        document, file_meta = test_document_with_file

        response = client.get(
            f"/documents/{document.id}/files/{file_meta.file_id}/download",
            params={"token": "invalid"},
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        assert response.status_code == 403
        assert "Invalid access token" in response.json()["detail"]

    def test_get_file_metadata_comprehensive(self, db: Session, test_user: User, test_document_with_file):
        """Test comprehensive file metadata retrieval."""
        document, file_meta = test_document_with_file

        with patch('services.document_storage.DocumentStorageService.retrieve_file') as mock_retrieve:
            mock_retrieve.return_value = MagicMock(
                file_meta=MagicMock(
                    file_id=file_meta.file_id,
                    original_filename="test.pdf",
                    file_size=1024,
                    checksum_sha256="abc123def456",
                    checksum_md5="xyz789",
                    file_integrity_verified=True,
                    last_accessed=datetime.utcnow(),
                    download_count=5,
                    dict=lambda: {
                        "file_id": file_meta.file_id,
                        "original_filename": "test.pdf",
                        "file_size": 1024
                    }
                ),
                access_granted=True
            )

            response = client.get(
                f"/documents/{document.id}/file-meta",
                params={
                    "include_checksums": True,
                    "include_access_history": True
                },
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["integrity_verified"] is True
        assert "checksums" in data
        assert data["checksums"]["sha256"] == "abc123def456"
        assert "access_history" in data


class TestDocumentExport:
    """Test document export functionality."""

    def test_export_pdf_with_annotations(self, db: Session, test_user: User, test_document_with_file):
        """Test PDF export with annotations and lineage."""
        document, _ = test_document_with_file

        export_request = DocumentExportRequest(
            export_format=ExportFormat.PDF_ANNOTATED,
            include_version_history=True,
            include_audit_trail=True,
            include_collaboration_data=True,
            watermark_config={
                "enabled": True,
                "text": "CONFIDENTIAL",
                "position": "diagonal"
            }
        )

        with patch('services.document_storage.DocumentStorageService.export_document') as mock_export:
            mock_export.return_value = MagicMock(
                export_id="export_123",
                export_format=ExportFormat.PDF_ANNOTATED,
                file_path="/exports/document_123_annotated.pdf",
                file_size=2048,
                download_url="https://storage.example.com/exports/export_123/document_123_annotated.pdf",
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )

            response = client.post(
                f"/documents/{document.id}/export",
                json=export_request.dict(),
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["export_id"] == "export_123"
        assert data["export_format"] == "pdf_annotated"
        assert "download_url" in data

    def test_export_structured_json_with_lineage(self, db: Session, test_user: User, test_document_with_file):
        """Test structured JSON export with complete lineage."""
        document, _ = test_document_with_file

        export_request = DocumentExportRequest(
            export_format=ExportFormat.JSON_STRUCTURED,
            include_version_history=True,
            include_audit_trail=True,
            include_collaboration_data=True,
            include_ai_annotations=True,
            lineage_preservation_level="comprehensive"
        )

        with patch('services.document_storage.DocumentStorageService.export_document') as mock_export:
            mock_export.return_value = MagicMock(
                export_id="export_456",
                export_format=ExportFormat.JSON_STRUCTURED,
                metadata_embedded=True,
                lineage_complete=True
            )

            response = client.post(
                f"/documents/{document.id}/export",
                json=export_request.dict(),
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata_embedded"] is True
        assert data["lineage_complete"] is True

    def test_export_archive_bundle(self, db: Session, test_user: User, test_document_with_file):
        """Test complete archive bundle export."""
        document, _ = test_document_with_file

        export_request = DocumentExportRequest(
            export_format=ExportFormat.ARCHIVE_BUNDLE,
            include_version_history=True,
            include_audit_trail=True,
            include_collaboration_data=True,
            include_ai_annotations=True,
            ada_compliance_level="full"
        )

        with patch('services.document_storage.DocumentStorageService.export_document') as mock_export:
            mock_export.return_value = MagicMock(
                export_id="export_789",
                export_format=ExportFormat.ARCHIVE_BUNDLE,
                bundle_contents=[
                    "document.pdf",
                    "document_history.json",
                    "audit_trail.json",
                    "collaboration_data.json",
                    "ai_annotations.json",
                    "manifest.json"
                ]
            )

            response = client.post(
                f"/documents/{document.id}/export",
                json=export_request.dict(),
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["bundle_contents"]) == 6
        assert "manifest.json" in data["bundle_contents"]

    def test_export_unauthorized_document(self, db: Session, test_user: User):
        """Test export rejection for unauthorized document."""
        # Create document in different organization
        document = Document(
            title="Unauthorized Document",
            organization_id=999,
            created_by_id=999
        )

        export_request = DocumentExportRequest(
            export_format=ExportFormat.PDF_CLEAN
        )

        response = client.post(
            f"/documents/{document.id}/export",
            json=export_request.dict(),
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        assert response.status_code == 403

    def test_download_export_file(self, db: Session, test_user: User):
        """Test downloading specific export file."""
        export_id = "export_123"
        filename = "document_annotated.pdf"

        # Create temporary export file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(b"Exported PDF content")
            temp_file_path = temp_file.name

        export_dir = os.path.dirname(temp_file_path)

        with patch('services.document_storage.DocumentStorageService.storage_root', export_dir):
            # Mock the export directory structure
            with patch('os.path.exists') as mock_exists:
                mock_exists.return_value = True
                with patch('os.path.join') as mock_join:
                    mock_join.return_value = temp_file_path

                    response = client.get(
                        f"/documents/exports/{export_id}/files/{filename}",
                        headers={"Authorization": f"Bearer {test_user.access_token}"}
                    )

        assert response.status_code == 200

        # Cleanup
        os.unlink(temp_file_path)


class TestCourtPackaging:
    """Test court packaging functionality."""

    def test_package_for_federal_district_court(self, db: Session, test_user: User, test_document_with_file):
        """Test packaging for federal district court."""
        document, _ = test_document_with_file

        packaging_request = CourtPackagingRequest(
            jurisdiction=JurisdictionType.FEDERAL_DISTRICT,
            case_info=CaseInfo(
                case_number="1:23-cv-00456",
                case_title="Smith v. Jones",
                court_name="United States District Court for the Northern District of California"
            ),
            attorney_info=AttorneyInfo(
                attorney_name="John Smith",
                bar_number="123456",
                law_firm="Smith & Associates",
                email="john@smithlaw.com",
                phone="555-123-4567"
            ),
            packaging_flags=PackagingFlags(
                include_table_of_contents=True,
                include_certificate_of_service=True,
                create_filing_package=True,
                apply_jurisdiction_formatting=True
            )
        )

        with patch('services.document_storage.DocumentStorageService.package_for_court') as mock_package:
            mock_package.return_value = MagicMock(
                package_id="package_123",
                jurisdiction=JurisdictionType.FEDERAL_DISTRICT,
                package_status="completed",
                validation_passed=True,
                package_file_path="/packages/package_123.zip",
                manifest_file_path="/packages/package_123_manifest.json",
                files_included=[
                    "document.pdf",
                    "table_of_contents.pdf",
                    "certificate_of_service.pdf",
                    "filing_manifest.xml"
                ]
            )

            response = client.post(
                f"/documents/{document.id}/package",
                json=packaging_request.dict(),
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["package_id"] == "package_123"
        assert data["validation_passed"] is True
        assert "filing_manifest.xml" in data["files_included"]

    def test_package_for_state_trial_court(self, db: Session, test_user: User, test_document_with_file):
        """Test packaging for state trial court."""
        document, _ = test_document_with_file

        packaging_request = CourtPackagingRequest(
            jurisdiction=JurisdictionType.STATE_TRIAL,
            case_info=CaseInfo(
                case_number="CV-2023-456789",
                case_title="Acme Corp v. Beta LLC",
                court_name="Superior Court of California, County of Santa Clara"
            ),
            attorney_info=AttorneyInfo(
                attorney_name="Jane Doe",
                bar_number="654321",
                law_firm="Doe Legal Group",
                email="jane@doelegal.com",
                phone="555-987-6543"
            ),
            packaging_flags=PackagingFlags(
                include_table_of_contents=False,  # Not required for state
                include_certificate_of_service=True,
                create_filing_package=False,  # Manual filing
                apply_jurisdiction_formatting=True
            )
        )

        with patch('services.document_storage.DocumentStorageService.package_for_court') as mock_package:
            mock_package.return_value = MagicMock(
                package_id="package_456",
                jurisdiction=JurisdictionType.STATE_TRIAL,
                package_status="completed",
                validation_passed=True,
                jurisdiction_compliant=True
            )

            response = client.post(
                f"/documents/{document.id}/package",
                json=packaging_request.dict(),
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["jurisdiction_compliant"] is True

    def test_package_validation_errors(self, db: Session, test_user: User, test_document_with_file):
        """Test court packaging validation errors."""
        document, _ = test_document_with_file

        # Invalid case number format for federal court
        packaging_request = CourtPackagingRequest(
            jurisdiction=JurisdictionType.FEDERAL_DISTRICT,
            case_info=CaseInfo(
                case_number="INVALID",  # Should be format like "1:23-cv-00456"
                case_title="Invalid Case",
                court_name="US District Court"
            ),
            attorney_info=AttorneyInfo(
                attorney_name="Test Attorney",
                bar_number="123",
                law_firm="Test Firm",
                email="invalid-email",  # Invalid email
                phone="123"  # Invalid phone
            ),
            packaging_flags=PackagingFlags()
        )

        with patch('services.document_storage.DocumentStorageService.package_for_court') as mock_package:
            mock_package.side_effect = ValidationError("Invalid case number format for federal court")

            response = client.post(
                f"/documents/{document.id}/package",
                json=packaging_request.dict(),
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert response.status_code == 400
        assert "Invalid case number format" in response.json()["detail"]

    def test_validate_package_request_pre_check(self, db: Session, test_user: User, test_document_with_file):
        """Test package request validation without creating package."""
        document, _ = test_document_with_file

        packaging_request = CourtPackagingRequest(
            jurisdiction=JurisdictionType.FEDERAL_DISTRICT,
            case_info=CaseInfo(
                case_number="1:23-cv-00456",
                case_title="Valid Case",
                court_name="US District Court"
            ),
            attorney_info=AttorneyInfo(
                attorney_name="Valid Attorney",
                bar_number="123456",
                law_firm="Valid Firm",
                email="valid@email.com",
                phone="555-123-4567"
            ),
            packaging_flags=PackagingFlags()
        )

        response = client.post(
            f"/documents/validate-package-request",
            params={"document_id": document.id},
            json=packaging_request.dict(),
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["jurisdiction_compliant"] is True
        assert "jurisdiction_rules" in data

    def test_download_court_package(self, db: Session, test_user: User):
        """Test downloading court package bundle."""
        package_id = "package_123"

        # Create temporary package zip file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            with zipfile.ZipFile(temp_file, 'w') as zip_file:
                zip_file.writestr("document.pdf", b"PDF content")
                zip_file.writestr("manifest.json", json.dumps({"files": ["document.pdf"]}))
            temp_file_path = temp_file.name

        package_dir = os.path.dirname(temp_file_path)

        with patch('services.document_storage.DocumentStorageService.storage_root', package_dir):
            with patch('os.listdir') as mock_listdir:
                mock_listdir.return_value = [os.path.basename(temp_file_path)]

                response = client.get(
                    f"/documents/packages/{package_id}/download",
                    headers={"Authorization": f"Bearer {test_user.access_token}"}
                )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

        # Cleanup
        os.unlink(temp_file_path)

    def test_download_package_manifest(self, db: Session, test_user: User):
        """Test downloading package manifest."""
        package_id = "package_123"

        # Create temporary manifest file
        manifest_data = {
            "package_id": package_id,
            "jurisdiction": "federal_district",
            "files": ["document.pdf", "certificate_of_service.pdf"],
            "created_at": datetime.utcnow().isoformat()
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(manifest_data, temp_file)
            temp_file_path = temp_file.name

        with patch('services.document_storage.DocumentStorageService.storage_root', os.path.dirname(temp_file_path)):
            with patch('os.path.exists') as mock_exists:
                mock_exists.return_value = True

                response = client.get(
                    f"/documents/packages/{package_id}/manifest",
                    headers={"Authorization": f"Bearer {test_user.access_token}"}
                )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Cleanup
        os.unlink(temp_file_path)


class TestStorageStatistics:
    """Test storage statistics and analytics."""

    def test_get_organization_storage_stats(self, db: Session, test_admin_user: User):
        """Test retrieving organization storage statistics."""
        with patch('services.document_storage.DocumentStorageService.get_storage_stats') as mock_stats:
            mock_stats.return_value = MagicMock(
                total_files=150,
                total_size_bytes=1024000000,  # 1GB
                files_by_format={"pdf": 100, "docx": 30, "txt": 20},
                uploads_last_30_days=25,
                exports_last_30_days=10,
                packages_last_30_days=5,
                storage_usage_percentage=65.5,
                average_file_size_mb=6.8
            )

            response = client.get(
                "/documents/storage/stats",
                headers={"Authorization": f"Bearer {test_admin_user.access_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 150
        assert data["storage_usage_percentage"] == 65.5
        assert data["files_by_format"]["pdf"] == 100

    def test_storage_stats_non_admin_rejection(self, db: Session, test_user: User):
        """Test storage stats rejection for non-admin users."""
        response = client.get(
            "/documents/storage/stats",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        assert response.status_code == 403
        assert "admin access required" in response.json()["detail"]


class TestJurisdictionSupport:
    """Test jurisdiction support and requirements."""

    def test_list_supported_jurisdictions(self):
        """Test listing all supported jurisdictions."""
        response = client.get("/documents/jurisdictions")

        assert response.status_code == 200
        data = response.json()
        assert "supported_jurisdictions" in data
        assert data["total_count"] > 0

        # Check federal district court is included
        federal_courts = [j for j in data["supported_jurisdictions"] if j["type"] == "federal_district"]
        assert len(federal_courts) == 1
        assert federal_courts[0]["supports_electronic_filing"] is True

    def test_jurisdiction_requirements_validation(self):
        """Test that jurisdiction requirements are properly defined."""
        response = client.get("/documents/jurisdictions")
        data = response.json()

        for jurisdiction in data["supported_jurisdictions"]:
            assert "type" in jurisdiction
            assert "name" in jurisdiction
            assert "supports_electronic_filing" in jurisdiction
            assert "max_file_size_mb" in jurisdiction
            assert "allowed_formats" in jurisdiction
            assert isinstance(jurisdiction["allowed_formats"], list)


class TestStorageHealth:
    """Test storage system health monitoring."""

    def test_storage_health_check_healthy(self):
        """Test storage health check when system is healthy."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True

            response = client.get("/documents/storage/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["directories_accessible"] is True
            assert data["encryption_available"] is True
            assert data["virus_scanning_enabled"] is True

    def test_storage_health_check_unhealthy(self):
        """Test storage health check when system has issues."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False

            response = client.get("/documents/storage/health")

            data = response.json()
            assert data["status"] == "unhealthy"
            assert "error" in data


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios."""

    def test_complete_document_lifecycle(self, db: Session, test_user: User, test_contract: Contract):
        """Test complete document lifecycle: upload → retrieve → export → package."""
        # 1. Create document
        document = Document(
            contract_id=test_contract.id,
            title="Contract Amendment",
            organization_id=test_user.organization_id,
            created_by_id=test_user.id
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # 2. Upload file
        pdf_content = b"%PDF-1.4\nContract content"

        with patch('services.document_storage.DocumentStorageService.upload_document') as mock_upload:
            mock_upload.return_value = MagicMock(
                file_id="file_lifecycle_test",
                virus_scan_passed=True,
                encrypted=True
            )

            upload_response = client.post(
                f"/documents/{document.id}/upload",
                files={"file": ("contract.pdf", BytesIO(pdf_content), "application/pdf")},
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert upload_response.status_code == 200
        file_id = upload_response.json()["file_id"]

        # 3. Retrieve file info
        with patch('services.document_storage.DocumentStorageService.retrieve_file') as mock_retrieve:
            mock_retrieve.return_value = MagicMock(
                file_meta=MagicMock(file_id=file_id),
                access_granted=True
            )

            retrieve_response = client.get(
                f"/documents/{document.id}/download",
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert retrieve_response.status_code == 200

        # 4. Export document
        export_request = DocumentExportRequest(
            export_format=ExportFormat.PDF_ANNOTATED,
            include_version_history=True,
            include_audit_trail=True
        )

        with patch('services.document_storage.DocumentStorageService.export_document') as mock_export:
            mock_export.return_value = MagicMock(
                export_id="export_lifecycle_test",
                export_format=ExportFormat.PDF_ANNOTATED
            )

            export_response = client.post(
                f"/documents/{document.id}/export",
                json=export_request.dict(),
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert export_response.status_code == 200
        export_id = export_response.json()["export_id"]

        # 5. Package for court
        packaging_request = CourtPackagingRequest(
            jurisdiction=JurisdictionType.FEDERAL_DISTRICT,
            case_info=CaseInfo(
                case_number="1:23-cv-12345",
                case_title="Contract Dispute",
                court_name="US District Court"
            ),
            attorney_info=AttorneyInfo(
                attorney_name="Test Attorney",
                bar_number="123456",
                law_firm="Test Firm",
                email="attorney@test.com",
                phone="555-123-4567"
            ),
            packaging_flags=PackagingFlags(
                include_table_of_contents=True,
                include_certificate_of_service=True
            )
        )

        with patch('services.document_storage.DocumentStorageService.package_for_court') as mock_package:
            mock_package.return_value = MagicMock(
                package_id="package_lifecycle_test",
                validation_passed=True,
                jurisdiction_compliant=True
            )

            package_response = client.post(
                f"/documents/{document.id}/package",
                json=packaging_request.dict(),
                headers={"Authorization": f"Bearer {test_user.access_token}"}
            )

        assert package_response.status_code == 200
        package_data = package_response.json()
        assert package_data["validation_passed"] is True
        assert package_data["jurisdiction_compliant"] is True

    def test_audit_trail_preservation(self, db: Session, test_user: User, test_document_with_file):
        """Test that audit trails are preserved through all operations."""
        document, _ = test_document_with_file

        # Mock audit service to track calls
        audit_calls = []

        def mock_audit_call(*args, **kwargs):
            audit_calls.append((args, kwargs))

        with patch('services.document_storage.audit_service.log_event', side_effect=mock_audit_call):
            # Upload
            with patch('services.document_storage.DocumentStorageService.upload_document') as mock_upload:
                mock_upload.return_value = MagicMock(file_id="audit_test")

                client.post(
                    f"/documents/{document.id}/upload",
                    files={"file": ("test.pdf", BytesIO(b"content"), "application/pdf")},
                    headers={"Authorization": f"Bearer {test_user.access_token}"}
                )

            # Export
            with patch('services.document_storage.DocumentStorageService.export_document') as mock_export:
                mock_export.return_value = MagicMock(export_id="audit_export")

                client.post(
                    f"/documents/{document.id}/export",
                    json={"export_format": "pdf_clean"},
                    headers={"Authorization": f"Bearer {test_user.access_token}"}
                )

        # Verify audit calls were made
        assert len(audit_calls) >= 2  # At least upload and export events


# Fixtures

@pytest.fixture
def test_document_with_file(db: Session, test_user: User, test_contract: Contract):
    """Create test document with file metadata."""
    document = Document(
        contract_id=test_contract.id,
        title="Test Document with File",
        organization_id=test_user.organization_id,
        created_by_id=test_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Mock file metadata
    file_meta = MagicMock(
        file_id="test_file_123",
        original_filename="test.pdf",
        file_size=1024,
        content_type="application/pdf",
        storage_path="/test/storage/test_file_123.pdf",
        checksum_sha256="abc123",
        encrypted=True
    )

    return document, file_meta


@pytest.fixture
def test_admin_user(db: Session, test_organization):
    """Create test admin user."""
    admin_user = User(
        email="admin@test.com",
        username="admin",
        organization_id=test_organization.id,
        is_admin=True,
        access_token="admin_token_123"
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user
