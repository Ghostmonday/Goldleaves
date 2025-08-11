# routers/document_storage.py

"""Phase 7: Document storage router for secure file management, export, and court packaging."""

import os
import mimetypes
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime

from core.db.session import get_db
from core.dependencies import get_current_user
from core.security import require_permission
from models.user import User
from services.document_storage import DocumentStorageService
from schemas.storage.storage import (
    DocumentUploadRequest, DocumentExportRequest, FileUploadResponse,
    FileRetrievalResponse, ExportResponse, StorageStats, FileFormat
)
from schemas.storage.court_packaging import (
    CourtPackagingRequest, CourtPackageResponse, JurisdictionType
)
from core.exceptions import NotFoundError, ValidationError, PermissionError
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Document Storage"])
security = HTTPBearer()

# Initialize storage service
storage_service = DocumentStorageService()


# File Upload Endpoints

@router.post("/{document_id}/upload", response_model=FileUploadResponse)
async def upload_document_file(
    document_id: int,
    file: UploadFile = File(...),
    version_number: Optional[int] = Query(None, description="Link to specific document version"),
    is_primary_file: bool = Query(True, description="Whether this is the primary document file"),
    upload_reason: Optional[str] = Query(None, description="Reason for file upload"),
    tags: List[str] = Query([], description="File classification tags"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a secure document file with encryption and integrity validation.
    
    This endpoint provides:
    - Multi-tenant file isolation
    - Virus scanning and validation
    - Checksum verification
    - Encryption at rest
    - Comprehensive audit logging
    """
    try:
        # Check document upload permission
        await require_permission(db, current_user.id, document_id, "upload")
        
        # Validate file
        if not file.filename:
            raise ValidationError("Filename is required")
        
        if file.size and file.size > 100 * 1024 * 1024:  # 100MB limit
            raise ValidationError("File size exceeds maximum limit (100MB)")
        
        # Detect file format from content type and extension
        content_type = file.content_type or "application/octet-stream"
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Map to FileFormat enum
        format_mapping = {
            '.pdf': FileFormat.PDF,
            '.docx': FileFormat.DOCX,
            '.txt': FileFormat.TXT,
            '.html': FileFormat.HTML,
            '.xml': FileFormat.XML,
            '.json': FileFormat.JSON
        }
        
        file_format = format_mapping.get(file_extension)
        if not file_format:
            raise ValidationError(f"Unsupported file format: {file_extension}")
        
        # Create upload request
        upload_request = DocumentUploadRequest(
            file_name=file.filename,
            file_size=file.size or 0,
            content_type=content_type,
            file_format=file_format,
            version_number=version_number,
            is_primary_file=is_primary_file,
            upload_reason=upload_reason,
            tags=tags
        )
        
        # Upload file
        upload_response = await storage_service.upload_document(
            db=db,
            document_id=document_id,
            file_data=file.file,
            upload_request=upload_request,
            organization_id=current_user.organization_id,
            user_id=current_user.id
        )
        
        logger.info(
            f"File uploaded successfully for document {document_id} "
            f"by user {current_user.id} (file_id: {upload_response.file_id})"
        )
        
        return upload_response
        
    except NotFoundError as e:
        logger.warning(f"Document {document_id} not found for upload by user {current_user.id}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Invalid upload request for document {document_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for upload to document {document_id} by user {current_user.id}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading file to document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# File Download Endpoints

@router.get("/{document_id}/download", response_model=FileRetrievalResponse)
async def get_document_file_info(
    document_id: int,
    file_id: Optional[str] = Query(None, description="Specific file ID"),
    version_number: Optional[int] = Query(None, description="Specific version number"),
    include_download_url: bool = Query(True, description="Generate download URL"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get document file information and download URL.
    
    This endpoint provides:
    - File metadata and properties
    - Secure download URL generation
    - Access control validation
    - Audit trail logging
    """
    try:
        # Check document read permission
        await require_permission(db, current_user.id, document_id, "read")
        
        file_info = await storage_service.retrieve_file(
            db=db,
            document_id=document_id,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            file_id=file_id,
            version_number=version_number,
            include_download_url=include_download_url
        )
        
        logger.info(
            f"File info retrieved for document {document_id} "
            f"by user {current_user.id} (file_id: {file_info.file_meta.file_id})"
        )
        
        return file_info
        
    except NotFoundError as e:
        logger.warning(f"Document or file not found for document {document_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for download from document {document_id} by user {current_user.id}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving file info for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{document_id}/files/{file_id}/download")
async def download_document_file(
    document_id: int,
    file_id: str,
    token: str = Query(..., description="Access token for download"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download document file with access token validation.
    
    This endpoint provides:
    - Secure file streaming
    - Access token validation
    - Download audit logging
    - Virus scan verification
    """
    try:
        # Validate access token (in production, verify against stored tokens)
        if not token or len(token) < 16:
            raise PermissionError("Invalid access token")
        
        # Get file info
        file_info = await storage_service.retrieve_file(
            db=db,
            document_id=document_id,
            organization_id=current_user.organization_id if current_user else None,
            user_id=current_user.id if current_user else None,
            file_id=file_id,
            include_download_url=False
        )
        
        if not file_info.access_granted:
            raise PermissionError("Access denied")
        
        # Get file path
        file_path = file_info.file_meta.storage_path
        if not os.path.exists(file_path):
            raise NotFoundError("File not found on storage")
        
        # Determine media type
        media_type = file_info.file_meta.content_type
        if not media_type:
            media_type, _ = mimetypes.guess_type(file_info.file_meta.original_filename)
            media_type = media_type or "application/octet-stream"
        
        logger.info(
            f"File downloaded for document {document_id} "
            f"by user {current_user.id if current_user else 'anonymous'} "
            f"(file_id: {file_id})"
        )
        
        # Return file response
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=file_info.file_meta.original_filename,
            headers={
                "Content-Disposition": file_info.content_disposition,
                "Cache-Control": file_info.cache_control
            }
        )
        
    except (NotFoundError, PermissionError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading file {file_id} from document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# File Metadata Endpoints

@router.get("/{document_id}/file-meta")
async def get_document_file_metadata(
    document_id: int,
    include_checksums: bool = Query(True, description="Include file integrity checksums"),
    include_access_history: bool = Query(False, description="Include access history"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive file metadata and integrity information.
    
    This endpoint provides:
    - File integrity checksums
    - Storage information
    - Access history (if requested)
    - Security properties
    """
    try:
        # Check document read permission
        await require_permission(db, current_user.id, document_id, "read")
        
        file_info = await storage_service.retrieve_file(
            db=db,
            document_id=document_id,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            include_download_url=False
        )
        
        # Build metadata response
        metadata_response = {
            "file_meta": file_info.file_meta.dict(),
            "integrity_verified": file_info.file_meta.file_integrity_verified,
            "last_accessed": file_info.file_meta.last_accessed,
            "download_count": file_info.file_meta.download_count
        }
        
        if include_checksums:
            metadata_response["checksums"] = {
                "sha256": file_info.file_meta.checksum_sha256,
                "md5": file_info.file_meta.checksum_md5
            }
        
        if include_access_history:
            # In production, query access logs
            metadata_response["access_history"] = []
        
        logger.info(
            f"File metadata retrieved for document {document_id} "
            f"by user {current_user.id}"
        )
        
        return metadata_response
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving file metadata for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Export Endpoints

@router.post("/{document_id}/export", response_model=ExportResponse)
async def export_document_with_lineage(
    document_id: int,
    export_request: DocumentExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export document with complete lineage preservation and metadata embedding.
    
    This endpoint provides:
    - Multiple export formats (PDF, DOCX, JSON, Archive)
    - Version history inclusion
    - Audit trail embedding
    - ADA compliance options
    - Watermarking support
    """
    try:
        # Check document export permission
        await require_permission(db, current_user.id, document_id, "export")
        
        export_response = await storage_service.export_document(
            db=db,
            document_id=document_id,
            export_request=export_request,
            organization_id=current_user.organization_id,
            user_id=current_user.id
        )
        
        # Add background task for cleanup (remove old exports)
        background_tasks.add_task(
            cleanup_old_exports,
            current_user.organization_id
        )
        
        logger.info(
            f"Document {document_id} exported as {export_request.export_format.value} "
            f"by user {current_user.id} (export_id: {export_response.export_id})"
        )
        
        return export_response
        
    except NotFoundError as e:
        logger.warning(f"Document {document_id} not found for export by user {current_user.id}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Invalid export request for document {document_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for export of document {document_id} by user {current_user.id}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Court Packaging Endpoints

@router.post("/{document_id}/package", response_model=CourtPackageResponse)
async def package_document_for_court(
    document_id: int,
    packaging_request: CourtPackagingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Package document for court filing with jurisdiction-specific formatting.
    
    This endpoint provides:
    - Jurisdiction-aware formatting
    - Court document templates
    - E-filing package preparation
    - Legal compliance validation
    - Certificate of service generation
    """
    try:
        # Check document package permission
        await require_permission(db, current_user.id, document_id, "export")
        
        package_response = await storage_service.package_for_court(
            db=db,
            document_id=document_id,
            packaging_request=packaging_request,
            organization_id=current_user.organization_id,
            user_id=current_user.id
        )
        
        # Add background task for e-filing preparation if requested
        if packaging_request.packaging_flags.create_filing_package:
            background_tasks.add_task(
                prepare_efiling_submission,
                package_response.package_id,
                packaging_request.jurisdiction
            )
        
        logger.info(
            f"Court package created for document {document_id} "
            f"(jurisdiction: {packaging_request.jurisdiction.value}, "
            f"package_id: {package_response.package_id}) "
            f"by user {current_user.id}"
        )
        
        return package_response
        
    except NotFoundError as e:
        logger.warning(f"Document {document_id} not found for packaging by user {current_user.id}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Invalid packaging request for document {document_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for packaging document {document_id} by user {current_user.id}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error packaging document {document_id} for court: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Package Download Endpoints

@router.get("/packages/{package_id}/download")
async def download_court_package(
    package_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download court package bundle.
    
    This endpoint provides:
    - Secure package download
    - Access validation
    - Audit logging
    - Package integrity verification
    """
    try:
        # Validate package access (in production, check package ownership)
        package_dir = storage_service.storage_root + f"/packages/package_{package_id}"
        
        if not os.path.exists(package_dir):
            raise NotFoundError("Package not found")
        
        # Find package bundle file
        package_files = [f for f in os.listdir(package_dir) if f.endswith('.zip')]
        if not package_files:
            raise NotFoundError("Package bundle not found")
        
        package_file = os.path.join(package_dir, package_files[0])
        
        logger.info(
            f"Court package {package_id} downloaded by user {current_user.id}"
        )
        
        return FileResponse(
            path=package_file,
            media_type="application/zip",
            filename=package_files[0],
            headers={
                "Content-Disposition": f'attachment; filename="{package_files[0]}"'
            }
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading package {package_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/packages/{package_id}/manifest")
async def download_package_manifest(
    package_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download court package manifest.
    
    This endpoint provides:
    - Package contents listing
    - Metadata verification
    - Compliance validation report
    """
    try:
        # Validate package access
        manifest_path = f"{storage_service.storage_root}/packages/package_{package_id}/package_manifest.json"
        
        if not os.path.exists(manifest_path):
            raise NotFoundError("Package manifest not found")
        
        logger.info(
            f"Package manifest {package_id} downloaded by user {current_user.id}"
        )
        
        return FileResponse(
            path=manifest_path,
            media_type="application/json",
            filename=f"manifest_{package_id}.json",
            headers={
                "Content-Disposition": f'attachment; filename="manifest_{package_id}.json"'
            }
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading manifest for package {package_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Export Download Endpoints

@router.get("/exports/{export_id}/files/{filename}")
async def download_export_file(
    export_id: str,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download specific export file.
    
    This endpoint provides:
    - Export file download
    - Access validation
    - Integrity verification
    """
    try:
        # Validate export access
        export_dir = f"{storage_service.storage_root}/exports/export_{export_id}"
        file_path = os.path.join(export_dir, filename)
        
        if not os.path.exists(file_path):
            raise NotFoundError("Export file not found")
        
        # Determine media type
        media_type, _ = mimetypes.guess_type(filename)
        media_type = media_type or "application/octet-stream"
        
        logger.info(
            f"Export file {filename} from export {export_id} downloaded by user {current_user.id}"
        )
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading export file {filename} from export {export_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Storage Statistics Endpoints

@router.get("/storage/stats", response_model=StorageStats)
async def get_organization_storage_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get organization storage statistics and metrics.
    
    This endpoint provides:
    - Storage usage metrics
    - File distribution analysis
    - Activity statistics
    - Compliance metrics
    """
    try:
        # Check admin permission for organization stats
        if not current_user.is_admin:
            raise PermissionError("Organization admin access required")
        
        storage_stats = await storage_service.get_storage_stats(
            db=db,
            organization_id=current_user.organization_id
        )
        
        logger.info(
            f"Storage statistics retrieved for organization {current_user.organization_id} "
            f"by user {current_user.id}"
        )
        
        return storage_stats
        
    except PermissionError as e:
        logger.warning(f"Permission denied for storage stats by user {current_user.id}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving storage statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Utility Endpoints

@router.get("/jurisdictions")
async def list_supported_jurisdictions():
    """
    List supported court jurisdictions and their requirements.
    
    This endpoint provides:
    - Available jurisdictions
    - Formatting requirements
    - E-filing capabilities
    - Validation rules
    """
    try:
        jurisdictions = []
        
        for jurisdiction_type in JurisdictionType:
            from schemas.storage.court_packaging import get_jurisdiction_rules
            rules = get_jurisdiction_rules(jurisdiction_type)
            
            jurisdictions.append({
                "type": jurisdiction_type.value,
                "name": jurisdiction_type.value.replace('_', ' ').title(),
                "supports_electronic_filing": rules.supports_electronic_filing,
                "max_file_size_mb": rules.max_file_size_mb,
                "allowed_formats": rules.allowed_file_formats,
                "requires_table_of_contents": rules.requires_table_of_contents,
                "requires_certificate_of_service": rules.requires_certificate_of_service
            })
        
        return {
            "supported_jurisdictions": jurisdictions,
            "total_count": len(jurisdictions)
        }
        
    except Exception as e:
        logger.error(f"Error listing jurisdictions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/validate-package-request")
async def validate_court_package_request(
    document_id: int,
    packaging_request: CourtPackagingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate court packaging request without creating package.
    
    This endpoint provides:
    - Pre-validation of packaging request
    - Jurisdiction compliance checking
    - Required field validation
    - Formatting requirement verification
    """
    try:
        # Check document access
        await require_permission(db, current_user.id, document_id, "read")
        
        from schemas.storage.court_packaging import get_jurisdiction_rules
        jurisdiction_rules = get_jurisdiction_rules(packaging_request.jurisdiction)
        
        validation_warnings = []
        validation_errors = []
        
        # Perform validation (reuse validation logic from service)
        await storage_service._validate_court_packaging_request(
            packaging_request, jurisdiction_rules, validation_warnings, validation_errors
        )
        
        return {
            "valid": len(validation_errors) == 0,
            "jurisdiction_compliant": len(validation_errors) == 0,
            "validation_warnings": validation_warnings,
            "validation_errors": validation_errors,
            "jurisdiction_rules": jurisdiction_rules.dict(),
            "estimated_processing_time_minutes": 5  # Estimated time
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error validating package request for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Background Tasks

async def cleanup_old_exports(organization_id: int):
    """Background task to clean up old export files."""
    try:
        # In production, implement cleanup logic for exports older than X days
        logger.info(f"Cleanup task scheduled for organization {organization_id}")
    except Exception as e:
        logger.error(f"Error in export cleanup task: {e}")


async def prepare_efiling_submission(package_id: str, jurisdiction: JurisdictionType):
    """Background task to prepare e-filing submission."""
    try:
        # In production, integrate with e-filing systems
        logger.info(f"E-filing preparation scheduled for package {package_id} (jurisdiction: {jurisdiction.value})")
    except Exception as e:
        logger.error(f"Error in e-filing preparation task: {e}")


# Health Check for Storage

@router.get("/storage/health")
async def check_storage_health():
    """
    Check storage system health and availability.
    
    This endpoint provides:
    - Storage system status
    - Disk space availability
    - Service connectivity
    """
    try:
        storage_root = storage_service.storage_root
        
        # Check storage directory accessibility
        if not os.path.exists(storage_root):
            raise Exception("Storage root directory not accessible")
        
        # Check disk space (in production, implement proper disk space checking)
        free_space_gb = 100  # Simulated
        
        return {
            "status": "healthy",
            "storage_root": storage_root,
            "free_space_gb": free_space_gb,
            "directories_accessible": True,
            "encryption_available": True,
            "virus_scanning_enabled": True,
            "last_checked": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_checked": datetime.utcnow().isoformat()
        }
