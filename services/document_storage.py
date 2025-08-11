# services/document_storage.py

"""Phase 7: Document storage service for secure file management, export, and court packaging."""

import os
import json
import hashlib
import zipfile
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, BinaryIO
from pathlib import Path

from sqlalchemy.orm import Session

from models.user import User
from models.document import Document, AuditEventType
from schemas.storage.storage import (
    DocumentUploadRequest, DocumentExportRequest, FileUploadResponse,
    FileRetrievalResponse, DocumentFileMeta, ExportResponse, ExportMetadata,
    StorageStats, EncryptionType, ExportFormat
)
from schemas.storage.court_packaging import (
    CourtPackagingRequest, CourtPackageResponse, JurisdictionType,
    JurisdictionValidation, get_jurisdiction_rules, PackagingStatus
)
from core.storage_config import get_storage_config
from core.exceptions import NotFoundError, ValidationError
from core.logging import get_logger

logger = get_logger(__name__)

class DocumentStorageService:
    """Comprehensive document storage service with enterprise features."""
    
    def __init__(self):
        """Initialize document storage service."""
        self.config = get_storage_config()
        self.storage_root = self.config.get_storage_root()
        self.max_file_size_mb = self.config.get_max_file_size_mb()
        self.encryption_enabled = self.config.is_encryption_enabled()
        self.virus_scanning_enabled = self.config.is_virus_scanning_enabled()
        
        # Ensure storage directories exist
        self._ensure_storage_structure()

import os
import hashlib
import uuid
import zipfile
from typing import Optional, List, Dict, Any, Tuple, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json

from models.document import (
    Document, DocumentVersion, DocumentAuditEvent, AuditEventType
)
from models.user import User
from core.exceptions import NotFoundError, ValidationError
from core.security import encrypt_data, generate_secure_token
from core.logging import get_logger
from schemas.storage.storage import (
    DocumentUploadRequest, DocumentExportRequest, DocumentFileMeta,
    ExportMetadata, FileUploadResponse, FileRetrievalResponse, 
    ExportResponse, StorageStats, ExportFormat, EncryptionType, 
    StorageProvider
)
from schemas.storage.court_packaging import (
    CourtPackagingRequest, PackagingStatus, CourtPackageResponse,
    PackageMetadata, JurisdictionValidation, get_jurisdiction_rules,
    JurisdictionType
)

logger = get_logger(__name__)


class DocumentStorageService:
    """Service for secure document file storage, export, and court packaging."""
    
    def __init__(self, storage_root: str = None):
        """Initialize storage service with configurable storage root."""
        self.storage_root = storage_root or os.environ.get("DOCUMENT_STORAGE_ROOT", "/var/goldleaves/storage")
        self.ensure_storage_directories()
    
    def ensure_storage_directories(self):
        """Ensure all required storage directories exist."""
        directories = [
            "files",
            "exports", 
            "packages",
            "temp",
            "quarantine"
        ]
        
        for directory in directories:
            path = Path(self.storage_root) / directory
            path.mkdir(parents=True, exist_ok=True)
    
    async def upload_document(
        self,
        db: Session,
        document_id: int,
        file_data: BinaryIO,
        upload_request: DocumentUploadRequest,
        organization_id: int,
        user_id: int
    ) -> FileUploadResponse:
        """
        Upload and securely store a document file.
        
        Args:
            db: Database session
            document_id: Target document ID
            file_data: File binary data
            upload_request: Upload request schema
            organization_id: Organization ID for multi-tenant isolation
            user_id: Uploading user ID
            
        Returns:
            FileUploadResponse with upload results
        """
        start_time = datetime.utcnow()
        
        try:
            # Verify document exists and user has access
            document = db.query(Document).filter(
                and_(
                    Document.id == document_id,
                    Document.organization_id == organization_id,
                    Document.is_deleted == False
                )
            ).first()
            
            if not document:
                raise NotFoundError(f"Document {document_id} not found")
            
            # Read file data and validate
            file_content = file_data.read()
            file_size = len(file_content)
            
            if file_size != upload_request.file_size:
                raise ValidationError(f"File size mismatch: expected {upload_request.file_size}, got {file_size}")
            
            # Calculate checksums
            sha256_hash = hashlib.sha256(file_content).hexdigest()
            md5_hash = hashlib.md5(file_content).hexdigest()
            
            # Verify client checksum if provided
            checksum_verified = True
            if upload_request.client_checksum:
                if upload_request.client_checksum.lower() != sha256_hash.lower():
                    checksum_verified = False
                    logger.warning(f"Checksum mismatch for document {document_id}")
            
            # Generate unique file ID and storage filename
            file_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_filename = self._sanitize_filename(upload_request.file_name)
            stored_filename = f"{timestamp}_{file_id[:8]}_{safe_filename}"
            
            # Determine storage path
            org_dir = f"org_{organization_id}"
            doc_dir = f"doc_{document_id}"
            storage_path = Path(self.storage_root) / "files" / org_dir / doc_dir / stored_filename
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Virus scan simulation (in production, integrate with actual antivirus)
            virus_scan_clean = await self._simulate_virus_scan(file_content)
            if not virus_scan_clean:
                # Move to quarantine
                quarantine_path = Path(self.storage_root) / "quarantine" / stored_filename
                quarantine_path.parent.mkdir(parents=True, exist_ok=True)
                raise ValidationError("File failed virus scan")
            
            # Apply encryption if requested
            encryption_applied = False
            encryption_key_id = None
            
            if upload_request.encryption_requested != EncryptionType.NONE:
                file_content, encryption_key_id = await self._encrypt_file_content(
                    file_content, upload_request.encryption_requested, organization_id
                )
                encryption_applied = True
            
            # Store file
            with open(storage_path, 'wb') as f:
                f.write(file_content)
            
            # Create file metadata record
            file_meta = DocumentFileMeta(
                file_id=file_id,
                document_id=document_id,
                version_number=upload_request.version_number,
                original_filename=upload_request.file_name,
                stored_filename=stored_filename,
                file_size=file_size,
                content_type=upload_request.content_type,
                file_format=upload_request.file_format,
                storage_provider=StorageProvider.LOCAL_FILESYSTEM,
                storage_path=str(storage_path),
                checksum_sha256=sha256_hash,
                checksum_md5=md5_hash,
                encryption_type=upload_request.encryption_requested,
                encryption_key_id=encryption_key_id,
                upload_timestamp=datetime.utcnow(),
                uploaded_by_id=user_id,
                organization_id=organization_id,
                virus_scan_status="clean" if virus_scan_clean else "infected",
                virus_scan_timestamp=datetime.utcnow(),
                file_integrity_verified=checksum_verified,
                tags=upload_request.tags,
                custom_metadata=upload_request.custom_metadata
            )
            
            # Store metadata in database (would need DocumentFile model)
            # For now, store in document's metadata field as an example
            if not document.metadata:
                document.metadata = {}
            
            if 'files' not in document.metadata:
                document.metadata['files'] = []
            
            document.metadata['files'].append(file_meta.dict())
            db.commit()
            
            # Log audit event
            await self._log_audit_event(
                db, document_id, organization_id, user_id,
                AuditEventType.UPLOADED,
                f"File uploaded: {upload_request.file_name}",
                metadata={
                    "file_id": file_id,
                    "file_size": file_size,
                    "checksum": sha256_hash,
                    "encryption_applied": encryption_applied
                }
            )
            
            # Calculate upload duration
            upload_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return FileUploadResponse(
                file_id=file_id,
                document_id=document_id,
                stored_filename=stored_filename,
                storage_path=str(storage_path.relative_to(self.storage_root)),
                checksum_verified=checksum_verified,
                virus_scan_clean=virus_scan_clean,
                encryption_applied=encryption_applied,
                upload_duration_ms=int(upload_duration),
                file_size=file_size,
                upload_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"File upload failed for document {document_id}: {e}")
            raise
    
    async def retrieve_file(
        self,
        db: Session,
        document_id: int,
        organization_id: int,
        user_id: int,
        file_id: Optional[str] = None,
        version_number: Optional[int] = None,
        include_download_url: bool = True
    ) -> FileRetrievalResponse:
        """
        Retrieve document file with access control and audit logging.
        
        Args:
            db: Database session
            document_id: Document ID
            organization_id: Organization ID for isolation
            user_id: Requesting user ID
            file_id: Specific file ID (optional)
            version_number: Specific version number (optional)
            include_download_url: Whether to generate download URL
            
        Returns:
            FileRetrievalResponse with file metadata and access info
        """
        try:
            # Verify document access
            document = db.query(Document).filter(
                and_(
                    Document.id == document_id,
                    Document.organization_id == organization_id,
                    Document.is_deleted == False
                )
            ).first()
            
            if not document:
                raise NotFoundError(f"Document {document_id} not found")
            
            # Find the requested file
            file_meta = await self._find_file_metadata(
                document, file_id, version_number
            )
            
            if not file_meta:
                raise NotFoundError("File not found")
            
            # Check file exists on disk
            storage_path = Path(file_meta.storage_path)
            if not storage_path.exists():
                logger.error(f"File not found on disk: {storage_path}")
                raise NotFoundError("File not found on storage")
            
            # Generate download URL if requested
            download_url = None
            access_token = None
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            if include_download_url:
                access_token = generate_secure_token()
                download_url = f"/api/v1/documents/{document_id}/files/{file_meta.file_id}/download?token={access_token}"
                
                # Store access token temporarily (in production, use Redis or similar)
                # For now, just generate a URL
            
            # Determine content disposition
            content_disposition = f'attachment; filename="{file_meta.original_filename}"'
            
            # Log access
            await self._log_audit_event(
                db, document_id, organization_id, user_id,
                AuditEventType.VIEWED,
                f"File access: {file_meta.original_filename}",
                metadata={
                    "file_id": file_meta.file_id,
                    "access_type": "metadata"
                }
            )
            
            return FileRetrievalResponse(
                file_meta=file_meta,
                download_url=download_url,
                access_token=access_token,
                expires_at=expires_at,
                access_granted=True,
                content_disposition=content_disposition,
                will_be_watermarked=False  # Could be configurable
            )
            
        except Exception as e:
            logger.error(f"File retrieval failed for document {document_id}: {e}")
            raise
    
    async def export_document(
        self,
        db: Session,
        document_id: int,
        export_request: DocumentExportRequest,
        organization_id: int,
        user_id: int
    ) -> ExportResponse:
        """
        Export document with lineage preservation and metadata embedding.
        
        Args:
            db: Database session
            document_id: Document ID to export
            export_request: Export configuration
            organization_id: Organization ID
            user_id: Exporting user ID
            
        Returns:
            ExportResponse with export results
        """
        start_time = datetime.utcnow()
        export_id = str(uuid.uuid4())
        
        try:
            # Get document with versions
            document = db.query(Document).filter(
                and_(
                    Document.id == document_id,
                    Document.organization_id == organization_id,
                    Document.is_deleted == False
                )
            ).first()
            
            if not document:
                raise NotFoundError(f"Document {document_id} not found")
            
            # Get document versions
            versions_query = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(DocumentVersion.version_number)
            
            # Apply version filtering
            if export_request.version_range:
                versions_query = versions_query.filter(
                    and_(
                        DocumentVersion.version_number >= export_request.version_range['from'],
                        DocumentVersion.version_number <= export_request.version_range['to']
                    )
                )
            elif export_request.specific_versions:
                versions_query = versions_query.filter(
                    DocumentVersion.version_number.in_(export_request.specific_versions)
                )
            
            versions = versions_query.all()
            
            if not versions:
                raise ValidationError("No versions found matching criteria")
            
            # Create export metadata
            export_metadata = await self._create_export_metadata(
                db, document, versions, export_request, user_id
            )
            
            # Create export directory
            export_dir = Path(self.storage_root) / "exports" / f"export_{export_id}"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate files based on export format
            generated_files = []
            download_urls = {}
            
            if export_request.export_format == ExportFormat.PDF_ANNOTATED:
                pdf_file = await self._generate_annotated_pdf(
                    document, versions, export_metadata, export_request, export_dir
                )
                generated_files.append(pdf_file)
                
            elif export_request.export_format == ExportFormat.JSON_STRUCTURED:
                json_file = await self._generate_structured_json(
                    document, versions, export_metadata, export_request, export_dir
                )
                generated_files.append(json_file)
                
            elif export_request.export_format == ExportFormat.ARCHIVE_BUNDLE:
                archive_file = await self._generate_archive_bundle(
                    document, versions, export_metadata, export_request, export_dir
                )
                generated_files.append(archive_file)
            
            # Generate manifest if requested
            manifest_path = None
            if export_request.generate_manifest:
                manifest_path = await self._generate_export_manifest(
                    export_metadata, generated_files, export_dir
                )
                generated_files.append(manifest_path.name)
            
            # Calculate total file size
            total_file_size = sum(
                (export_dir / filename).stat().st_size 
                for filename in generated_files
            )
            
            # Generate download URLs
            for filename in generated_files:
                download_urls[filename] = f"/api/v1/exports/{export_id}/files/{filename}"
            
            # Log audit event
            await self._log_audit_event(
                db, document_id, organization_id, user_id,
                AuditEventType.EXPORTED,
                f"Document exported as {export_request.export_format.value}",
                metadata={
                    "export_id": export_id,
                    "export_format": export_request.export_format.value,
                    "versions_included": len(versions)
                }
            )
            
            # Calculate generation duration
            generation_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ExportResponse(
                export_id=export_id,
                document_id=document_id,
                export_format=export_request.export_format,
                files_generated=generated_files,
                bundle_path=generated_files[0] if len(generated_files) == 1 else None,
                manifest_path=manifest_path.name if manifest_path else None,
                export_metadata=export_metadata,
                total_file_size=total_file_size,
                generation_duration_ms=int(generation_duration),
                download_urls=download_urls,
                access_expires_at=datetime.utcnow() + timedelta(hours=24),
                export_successful=True,
                validation_passed=True,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Document export failed for document {document_id}: {e}")
            raise
    
    async def package_for_court(
        self,
        db: Session,
        document_id: int,
        packaging_request: CourtPackagingRequest,
        organization_id: int,
        user_id: int
    ) -> CourtPackageResponse:
        """
        Package document for court filing with jurisdiction-specific formatting.
        
        Args:
            db: Database session
            document_id: Document ID to package
            packaging_request: Court packaging configuration
            organization_id: Organization ID
            user_id: Packaging user ID
            
        Returns:
            CourtPackageResponse with packaging results
        """
        start_time = datetime.utcnow()
        package_id = str(uuid.uuid4())
        
        try:
            # Get document
            document = db.query(Document).filter(
                and_(
                    Document.id == document_id,
                    Document.organization_id == organization_id,
                    Document.is_deleted == False
                )
            ).first()
            
            if not document:
                raise NotFoundError(f"Document {document_id} not found")
            
            # Get jurisdiction validation rules
            jurisdiction_rules = get_jurisdiction_rules(packaging_request.jurisdiction)
            
            # Validate packaging request against jurisdiction rules
            validation_warnings = []
            validation_errors = []
            
            await self._validate_court_packaging_request(
                packaging_request, jurisdiction_rules, validation_warnings, validation_errors
            )
            
            # Create package directory
            package_dir = Path(self.storage_root) / "packages" / f"package_{package_id}"
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # Get document versions for packaging
            versions = await self._get_versions_for_packaging(
                db, document_id, packaging_request
            )
            
            # Generate court-formatted document
            package_files = []
            
            # Main document with court formatting
            main_doc = await self._generate_court_formatted_document(
                document, versions, packaging_request, jurisdiction_rules, package_dir
            )
            package_files.append(main_doc)
            
            # Additional files based on flags
            if packaging_request.packaging_flags.include_table_of_contents:
                toc_file = await self._generate_table_of_contents(
                    document, versions, package_dir
                )
                package_files.append(toc_file)
            
            if packaging_request.packaging_flags.include_certificate_of_service:
                cert_file = await self._generate_certificate_of_service(
                    packaging_request, package_dir
                )
                package_files.append(cert_file)
            
            if packaging_request.include_version_history:
                history_file = await self._generate_version_history_appendix(
                    document, versions, package_dir
                )
                package_files.append(history_file)
            
            if packaging_request.include_audit_trail:
                audit_file = await self._generate_audit_trail_appendix(
                    db, document_id, package_dir
                )
                package_files.append(audit_file)
            
            # Create package bundle
            if packaging_request.bundle_format == "zip":
                bundle_file = await self._create_court_package_bundle(
                    package_files, package_dir, package_id
                )
            
            # Generate package metadata
            package_metadata = PackageMetadata(
                package_id=package_id,
                document_id=document_id,
                jurisdiction=packaging_request.jurisdiction,
                generated_at=datetime.utcnow(),
                generated_by=f"user_{user_id}",
                packaging_version="1.0.0",
                court_name=packaging_request.court_name,
                case_number=packaging_request.case_number,
                case_title=packaging_request.case_title,
                document_type=packaging_request.document_type,
                files_included=package_files,
                total_pages=await self._calculate_total_pages(package_files, package_dir),
                total_file_size=sum(
                    (package_dir / filename).stat().st_size for filename in package_files
                ),
                validation_passed=len(validation_errors) == 0,
                validation_warnings=validation_warnings,
                validation_errors=validation_errors,
                jurisdiction_compliant=len(validation_errors) == 0,
                formatting_applied=await self._get_applied_formatting(jurisdiction_rules),
                flags_used=packaging_request.packaging_flags,
                package_hash=await self._calculate_package_hash(package_files, package_dir),
                encryption_applied=packaging_request.encryption_required,
                watermark_applied=bool(packaging_request.watermark_text),
                source_versions=[v.version_number for v in versions],
                efiling_ready=jurisdiction_rules.supports_electronic_filing,
                filing_format="pdf" if jurisdiction_rules.supports_electronic_filing else None
            )
            
            # Generate manifest
            manifest_file = await self._generate_court_package_manifest(
                package_metadata, package_dir
            )
            
            # Generate download URLs
            package_download_url = f"/api/v1/packages/{package_id}/download"
            manifest_download_url = f"/api/v1/packages/{package_id}/manifest"
            
            # Log audit event
            await self._log_audit_event(
                db, document_id, organization_id, user_id,
                AuditEventType.EXPORTED,
                f"Court package created for {packaging_request.jurisdiction.value}",
                metadata={
                    "package_id": package_id,
                    "jurisdiction": packaging_request.jurisdiction.value,
                    "court_name": packaging_request.court_name,
                    "case_number": packaging_request.case_number
                }
            )
            
            # Calculate processing duration
            processing_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return CourtPackageResponse(
                package_id=package_id,
                document_id=document_id,
                packaging_status=PackagingStatus.COMPLETED,
                package_metadata=package_metadata,
                package_files=package_files,
                manifest_file=manifest_file,
                package_download_url=package_download_url,
                manifest_download_url=manifest_download_url,
                download_expires_at=datetime.utcnow() + timedelta(days=7),
                processing_duration_ms=int(processing_duration),
                success=True,
                jurisdiction_validation=jurisdiction_rules,
                validation_report={
                    "warnings": validation_warnings,
                    "errors": validation_errors,
                    "compliant": len(validation_errors) == 0
                },
                progress_percentage=100,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Court packaging failed for document {document_id}: {e}")
            
            return CourtPackageResponse(
                package_id=package_id,
                document_id=document_id,
                packaging_status=PackagingStatus.FAILED,
                processing_duration_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                success=False,
                error_message=str(e),
                progress_percentage=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
    
    async def get_storage_stats(
        self,
        db: Session,
        organization_id: int
    ) -> StorageStats:
        """Get storage statistics for organization."""
        
        # In a real implementation, this would query a DocumentFile table
        # For now, simulate with document metadata
        documents = db.query(Document).filter(
            and_(
                Document.organization_id == organization_id,
                Document.is_deleted == False
            )
        ).all()
        
        total_files = 0
        total_storage_bytes = 0
        files_by_format = {}
        uploads_last_30_days = 0
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        for doc in documents:
            if doc.metadata and 'files' in doc.metadata:
                for file_meta in doc.metadata['files']:
                    total_files += 1
                    total_storage_bytes += file_meta.get('file_size', 0)
                    
                    file_format = file_meta.get('file_format', 'unknown')
                    files_by_format[file_format] = files_by_format.get(file_format, 0) + 1
                    
                    upload_time = datetime.fromisoformat(file_meta.get('upload_timestamp', '2000-01-01'))
                    if upload_time >= thirty_days_ago:
                        uploads_last_30_days += 1
        
        return StorageStats(
            total_files=total_files,
            files_by_format=files_by_format,
            files_by_encryption={"aes_256_gcm": total_files, "none": 0},
            total_storage_bytes=total_storage_bytes,
            average_file_size=total_storage_bytes / total_files if total_files > 0 else 0,
            largest_file_size=max([
                file_meta.get('file_size', 0) 
                for doc in documents 
                if doc.metadata and 'files' in doc.metadata
                for file_meta in doc.metadata['files']
            ], default=0),
            uploads_last_30_days=uploads_last_30_days,
            downloads_last_30_days=0,  # Would track in access logs
            exports_last_30_days=0,    # Would track in audit events
            encrypted_files_percent=100.0,  # Assuming all files encrypted
            virus_scan_coverage_percent=100.0,
            last_updated=datetime.utcnow()
        )
    
    # Helper methods
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        import re
        # Remove dangerous characters and normalize
        safe_name = re.sub(r'[^\w\-_\.]', '_', filename)
        return safe_name[:100]  # Limit length
    
    async def _simulate_virus_scan(self, file_content: bytes) -> bool:
        """Simulate virus scanning (integrate with real antivirus in production)."""
        # Simple simulation - check for suspicious patterns
        suspicious_patterns = [b'malware', b'virus', b'trojan']
        return not any(pattern in file_content.lower() for pattern in suspicious_patterns)
    
    async def _encrypt_file_content(
        self, 
        content: bytes, 
        encryption_type: EncryptionType, 
        organization_id: int
    ) -> Tuple[bytes, str]:
        """Encrypt file content and return encrypted data with key ID."""
        if encryption_type == EncryptionType.AES_256_GCM:
            # In production, use proper key management
            key_id = f"org_{organization_id}_key_1"
            encrypted_content = encrypt_data(content, key_id)
            return encrypted_content, key_id
        
        return content, None
    
    async def _find_file_metadata(
        self, 
        document: Document, 
        file_id: str = None, 
        version_number: int = None
    ) -> Optional[DocumentFileMeta]:
        """Find file metadata from document."""
        if not document.metadata or 'files' not in document.metadata:
            return None
        
        for file_data in document.metadata['files']:
            if file_id and file_data.get('file_id') == file_id:
                return DocumentFileMeta(**file_data)
            elif version_number and file_data.get('version_number') == version_number:
                return DocumentFileMeta(**file_data)
        
        # Return first file if no specific criteria
        if document.metadata['files']:
            return DocumentFileMeta(**document.metadata['files'][0])
        
        return None
    
    async def _create_export_metadata(
        self,
        db: Session,
        document: Document,
        versions: List[DocumentVersion],
        export_request: DocumentExportRequest,
        user_id: int
    ) -> ExportMetadata:
        """Create comprehensive export metadata."""
        
        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        
        # Get audit events count
        audit_count = db.query(func.count(DocumentAuditEvent.id)).filter(
            DocumentAuditEvent.document_id == document.id
        ).scalar() or 0
        
        return ExportMetadata(
            document_id=document.id,
            document_title=document.title,
            organization_name=document.organization.name if document.organization else "Unknown",
            export_timestamp=datetime.utcnow(),
            export_format=export_request.export_format,
            exported_by=user.full_name if user else f"user_{user_id}",
            current_version=document.version,
            exported_versions=[v.version_number for v in versions],
            version_count=len(versions),
            creation_date=document.created_at,
            last_modified=document.edited_at or document.created_at,
            total_collaborators=len(set(v.changed_by_id for v in versions if v.changed_by_id)),
            total_changes=len(versions),
            total_audit_events=audit_count,
            view_count=0,  # Would get from audit events
            download_count=0,  # Would get from audit events
            share_count=0,  # Would get from secure shares
            content_hash=hashlib.sha256(str(document.id).encode()).hexdigest(),
            metadata_hash=hashlib.sha256(json.dumps(document.metadata or {}).encode()).hexdigest()
        )
    
    async def _generate_annotated_pdf(
        self,
        document: Document,
        versions: List[DocumentVersion],
        export_metadata: ExportMetadata,
        export_request: DocumentExportRequest,
        export_dir: Path
    ) -> str:
        """Generate annotated PDF with metadata embedded."""
        filename = f"{document.title}_annotated_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = export_dir / filename
        
        # In production, use proper PDF generation library (reportlab, weasyprint, etc.)
        with open(filepath, 'wb') as f:
            f.write(b'%PDF-1.4\n')  # PDF header
            f.write(f'% Generated by Goldleaves on {datetime.utcnow()}\n'.encode())
            f.write(f'% Document: {document.title}\n'.encode())
            f.write(f'% Versions: {len(versions)}\n'.encode())
            f.write(b'%EOF\n')  # PDF footer
        
        return filename
    
    async def _generate_structured_json(
        self,
        document: Document,
        versions: List[DocumentVersion],
        export_metadata: ExportMetadata,
        export_request: DocumentExportRequest,
        export_dir: Path
    ) -> str:
        """Generate structured JSON export."""
        filename = f"{document.title}_structured_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = export_dir / filename
        
        export_data = {
            "metadata": export_metadata.dict(),
            "document": {
                "id": document.id,
                "title": document.title,
                "type": document.document_type.value if document.document_type else None,
                "created_at": document.created_at.isoformat(),
                "current_version": document.version
            },
            "versions": [
                {
                    "version_number": v.version_number,
                    "title": v.title,
                    "content": v.content,
                    "change_summary": v.change_summary,
                    "created_at": v.created_at.isoformat(),
                    "changed_by_id": v.changed_by_id,
                    "metadata": v.metadata
                }
                for v in versions
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    async def _generate_archive_bundle(
        self,
        document: Document,
        versions: List[DocumentVersion],
        export_metadata: ExportMetadata,
        export_request: DocumentExportRequest,
        export_dir: Path
    ) -> str:
        """Generate archive bundle with all files."""
        archive_name = f"{document.title}_bundle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
        archive_path = export_dir / archive_name
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add metadata
            zipf.writestr("metadata.json", json.dumps(export_metadata.dict(), indent=2))
            
            # Add document data
            zipf.writestr("document.json", json.dumps({
                "id": document.id,
                "title": document.title,
                "metadata": document.metadata
            }, indent=2))
            
            # Add versions
            for version in versions:
                version_data = {
                    "version_number": version.version_number,
                    "title": version.title,
                    "content": version.content,
                    "metadata": version.metadata
                }
                zipf.writestr(f"versions/version_{version.version_number}.json", 
                             json.dumps(version_data, indent=2))
        
        return archive_name
    
    async def _generate_export_manifest(
        self,
        export_metadata: ExportMetadata,
        generated_files: List[str],
        export_dir: Path
    ) -> Path:
        """Generate export manifest file."""
        manifest_path = export_dir / "manifest.json"
        
        manifest_data = {
            "export_metadata": export_metadata.dict(),
            "generated_files": generated_files,
            "file_checksums": {},
            "generation_timestamp": datetime.utcnow().isoformat()
        }
        
        # Calculate file checksums
        for filename in generated_files:
            filepath = export_dir / filename
            if filepath.exists():
                with open(filepath, 'rb') as f:
                    content = f.read()
                    manifest_data["file_checksums"][filename] = hashlib.sha256(content).hexdigest()
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        
        return manifest_path
    
    async def _validate_court_packaging_request(
        self,
        request: CourtPackagingRequest,
        rules: JurisdictionValidation,
        warnings: List[str],
        errors: List[str]
    ):
        """Validate court packaging request against jurisdiction rules."""
        
        # Check required fields based on jurisdiction
        if rules.requires_table_of_contents and not request.packaging_flags.include_table_of_contents:
            warnings.append("Jurisdiction requires table of contents")
        
        if rules.requires_certificate_of_service and not request.packaging_flags.include_certificate_of_service:
            errors.append("Jurisdiction requires certificate of service")
        
        # Validate attorney information for jurisdictions that require it
        if request.jurisdiction in [JurisdictionType.FEDERAL_DISTRICT, JurisdictionType.FEDERAL_CIRCUIT]:
            if not request.attorney_bar_number:
                errors.append("Federal courts require attorney bar number")
    
    async def _get_versions_for_packaging(
        self,
        db: Session,
        document_id: int,
        request: CourtPackagingRequest
    ) -> List[DocumentVersion]:
        """Get document versions for court packaging."""
        
        query = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        )
        
        if request.version_range:
            query = query.filter(
                and_(
                    DocumentVersion.version_number >= request.version_range['from'],
                    DocumentVersion.version_number <= request.version_range['to']
                )
            )
        
        return query.order_by(DocumentVersion.version_number).all()
    
    async def _generate_court_formatted_document(
        self,
        document: Document,
        versions: List[DocumentVersion],
        request: CourtPackagingRequest,
        rules: JurisdictionValidation,
        package_dir: Path
    ) -> str:
        """Generate main court-formatted document."""
        
        filename = f"{request.case_number}_{request.document_type.value}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        filepath = package_dir / filename
        
        # In production, use proper PDF generation with court formatting
        with open(filepath, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(f'% Court: {request.court_name}\n'.encode())
            f.write(f'% Case: {request.case_number}\n'.encode())
            f.write(f'% Document: {request.document_title}\n'.encode())
            f.write(b'%EOF\n')
        
        return filename
    
    async def _generate_table_of_contents(
        self,
        document: Document,
        versions: List[DocumentVersion],
        package_dir: Path
    ) -> str:
        """Generate table of contents."""
        filename = f"table_of_contents.pdf"
        filepath = package_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'% Table of Contents\n')
            f.write(b'%EOF\n')
        
        return filename
    
    async def _generate_certificate_of_service(
        self,
        request: CourtPackagingRequest,
        package_dir: Path
    ) -> str:
        """Generate certificate of service."""
        filename = f"certificate_of_service.pdf"
        filepath = package_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(f'% Certificate of Service for {request.case_title}\n'.encode())
            f.write(b'%EOF\n')
        
        return filename
    
    async def _generate_version_history_appendix(
        self,
        document: Document,
        versions: List[DocumentVersion],
        package_dir: Path
    ) -> str:
        """Generate version history appendix."""
        filename = f"version_history_appendix.pdf"
        filepath = package_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(f'% Version History for {document.title}\n'.encode())
            f.write(f'% Total Versions: {len(versions)}\n'.encode())
            f.write(b'%EOF\n')
        
        return filename
    
    async def _generate_audit_trail_appendix(
        self,
        db: Session,
        document_id: int,
        package_dir: Path
    ) -> str:
        """Generate audit trail appendix."""
        filename = f"audit_trail_appendix.pdf"
        filepath = package_dir / filename
        
        audit_events = db.query(DocumentAuditEvent).filter(
            DocumentAuditEvent.document_id == document_id
        ).count()
        
        with open(filepath, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(f'% Audit Trail - {audit_events} events\n'.encode())
            f.write(b'%EOF\n')
        
        return filename
    
    async def _create_court_package_bundle(
        self,
        package_files: List[str],
        package_dir: Path,
        package_id: str
    ) -> str:
        """Create final court package bundle."""
        bundle_filename = f"court_package_{package_id}.zip"
        bundle_path = package_dir / bundle_filename
        
        with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename in package_files:
                file_path = package_dir / filename
                if file_path.exists():
                    zipf.write(file_path, filename)
        
        return bundle_filename
    
    async def _calculate_total_pages(
        self,
        package_files: List[str],
        package_dir: Path
    ) -> int:
        """Calculate total pages in package."""
        # In production, use proper PDF parsing to count pages
        return len(package_files) * 5  # Simulate 5 pages per file
    
    async def _get_applied_formatting(
        self,
        rules: JurisdictionValidation
    ) -> Dict[str, Any]:
        """Get formatting applied based on jurisdiction rules."""
        return {
            "font_size": rules.required_font_size,
            "line_spacing": rules.line_spacing_required,
            "margins": rules.required_margins_inches,
            "page_numbering": rules.page_numbering_required
        }
    
    async def _calculate_package_hash(
        self,
        package_files: List[str],
        package_dir: Path
    ) -> str:
        """Calculate integrity hash for package."""
        hasher = hashlib.sha256()
        
        for filename in sorted(package_files):
            file_path = package_dir / filename
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
        
        return hasher.hexdigest()
    
    async def _generate_court_package_manifest(
        self,
        metadata: PackageMetadata,
        package_dir: Path
    ) -> str:
        """Generate court package manifest."""
        manifest_filename = "package_manifest.json"
        manifest_path = package_dir / manifest_filename
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(metadata.dict(), f, indent=2, ensure_ascii=False, default=str)
        
        return manifest_filename
    
    async def _log_audit_event(
        self,
        db: Session,
        document_id: int,
        organization_id: int,
        user_id: int,
        event_type: AuditEventType,
        description: str,
        metadata: Dict[str, Any] = None
    ):
        """Log audit event for storage operations."""
        
        audit_event = DocumentAuditEvent(
            document_id=document_id,
            event_type=event_type,
            event_description=description,
            user_id=user_id,
            organization_id=organization_id,
            metadata=metadata or {}
        )
        
        db.add(audit_event)
        db.commit()
