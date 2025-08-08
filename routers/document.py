# routers/document.py

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from core.db.session import get_db
from core.dependencies import get_current_user, get_current_organization
from routers.dependencies import require_permission
from routers.contract import RouterContract, RouterTags, register_router
from models.user import User, Organization
from services.document import DocumentService
from schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentFilter,
    DocumentStats, DocumentPrediction, PredictionIngest, 
    DocumentCorrection, DocumentBulkAction, DocumentBulkResult,
    DocumentAudit, DocumentSearchResponse, DocumentPermissionCheck
)


class DocumentRouter(RouterContract):
    """Document management router with AI prediction support."""
    
    def __init__(self):
        self._router = APIRouter()
        self._prefix = "/documents"
        self._tags = ["documents"]
        self.configure_routes()
        register_router("document", self)
    
    @property
    def router(self) -> APIRouter:
        """FastAPI router instance."""
        return self._router
    
    @property 
    def prefix(self) -> str:
        """URL prefix for this router."""
        return self._prefix
    
    @property
    def tags(self) -> list:
        """OpenAPI tags for this router."""
        return self._tags
    
    def configure_routes(self) -> None:
        """Configure all document routes."""
        self._configure_document_crud()
        self._configure_prediction_endpoints()
        self._configure_correction_endpoints()
        self._configure_audit_endpoints()
        self._configure_search_endpoints()
        self._configure_bulk_operations()
        self._configure_sharing_endpoints()
    
    def _configure_document_crud(self) -> None:
        """Configure document CRUD endpoints."""
        
        @self._router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
        async def create_document(
            *,
            db: Session = Depends(get_db),
            document_data: DocumentCreate,
            current_user: User = Depends(get_current_user),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:create"))
        ):
            """Create a new document."""
            try:
                document = DocumentService.create_document(
                    db=db,
                    document_data=document_data,
                    organization_id=organization.id,
                    created_by_id=current_user.id
                )
                return DocumentResponse.from_orm(document)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self._router.get("/", response_model=Dict[str, Any])
        async def list_documents(
            *,
            db: Session = Depends(get_db),
            skip: int = Query(0, ge=0, description="Number of records to skip"),
            limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
            search: Optional[str] = Query(None, description="Search term for title, content, or description"),
            document_type: Optional[str] = Query(None, description="Filter by document type"),
            status: Optional[str] = Query(None, description="Filter by document status"),
            confidentiality: Optional[str] = Query(None, description="Filter by confidentiality level"),
            prediction_status: Optional[str] = Query(None, description="Filter by prediction status"),
            case_id: Optional[int] = Query(None, description="Filter by case ID"),
            client_id: Optional[int] = Query(None, description="Filter by client ID"),
            created_by_id: Optional[int] = Query(None, description="Filter by creator"),
            tags: Optional[List[str]] = Query(None, description="Filter by tags"),
            legal_hold: Optional[bool] = Query(None, description="Filter by legal hold status"),
            min_prediction_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum prediction score"),
            max_prediction_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum prediction score"),
            needs_review: Optional[bool] = Query(None, description="Filter documents needing review"),
            has_content: Optional[bool] = Query(None, description="Filter by content presence"),
            has_predictions: Optional[bool] = Query(None, description="Filter by prediction presence"),
            order_by: str = Query("created_at", description="Field to order by"),
            order_direction: str = Query("desc", regex="^(asc|desc)$", description="Order direction"),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:read"))
        ):
            """List documents with filtering and pagination."""
            
            # Build filters
            filters = DocumentFilter(
                search=search,
                document_type=document_type,
                status=status,
                confidentiality=confidentiality,
                prediction_status=prediction_status,
                case_id=case_id,
                client_id=client_id,
                created_by_id=created_by_id,
                tags=tags,
                legal_hold=legal_hold,
                min_prediction_score=min_prediction_score,
                max_prediction_score=max_prediction_score,
                needs_review=needs_review,
                has_content=has_content,
                has_predictions=has_predictions
            )
            
            documents, total = DocumentService.list_documents(
                db=db,
                organization_id=organization.id,
                filters=filters,
                skip=skip,
                limit=limit,
                order_by=order_by,
                order_direction=order_direction
            )
            
            return {
                "documents": [DocumentResponse.from_orm(doc) for doc in documents],
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": total > skip + limit
            }

        @self._router.get("/{document_id}", response_model=DocumentResponse)
        async def get_document(
            *,
            db: Session = Depends(get_db),
            document_id: int = Path(..., description="Document ID"),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:read"))
        ):
            """Get a specific document."""
            document = DocumentService.get_document(db, document_id, organization.id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            return DocumentResponse.from_orm(document)

        @self._router.put("/{document_id}", response_model=DocumentResponse)
        async def update_document(
            *,
            db: Session = Depends(get_db),
            document_id: int = Path(..., description="Document ID"),
            document_update: DocumentUpdate,
            current_user: User = Depends(get_current_user),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:update"))
        ):
            """Update a document."""
            try:
                document = DocumentService.update_document(
                    db=db,
                    document_id=document_id,
                    document_update=document_update,
                    organization_id=organization.id,
                    updated_by_id=current_user.id
                )
                if not document:
                    raise HTTPException(status_code=404, detail="Document not found")
                return DocumentResponse.from_orm(document)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self._router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete_document(
            *,
            db: Session = Depends(get_db),
            document_id: int = Path(..., description="Document ID"),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:delete"))
        ):
            """Delete a document."""
            success = DocumentService.delete_document(db, document_id, organization.id)
            if not success:
                raise HTTPException(status_code=404, detail="Document not found")
    
    def _configure_prediction_endpoints(self) -> None:
        """Configure AI prediction endpoints."""
        
        @self._router.post("/{document_id}/predict", response_model=DocumentResponse)
        async def ingest_prediction(
            *,
            db: Session = Depends(get_db),
            document_id: int = Path(..., description="Document ID"),
            prediction_ingest: PredictionIngest,
            current_user: User = Depends(get_current_user),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:predict"))
        ):
            """Ingest AI prediction data for a document."""
            try:
                document = DocumentService.ingest_prediction(
                    db=db,
                    document_id=document_id,
                    prediction_ingest=prediction_ingest,
                    organization_id=organization.id,
                    ingested_by_id=current_user.id
                )
                return DocumentResponse.from_orm(document)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self._router.get("/{document_id}/predictions", response_model=DocumentPrediction)
        async def get_predictions(
            *,
            db: Session = Depends(get_db),
            document_id: int = Path(..., description="Document ID"),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:read"))
        ):
            """Get AI predictions for a document."""
            document = DocumentService.get_document(db, document_id, organization.id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            if not document.ai_predictions:
                raise HTTPException(status_code=404, detail="No predictions found for this document")
            
            # Convert stored predictions back to schema format
            predictions_data = document.ai_predictions
            return DocumentPrediction(
                model_name=predictions_data.get("model_name", "unknown"),
                model_version=predictions_data.get("model_version", "unknown"),
                prediction_timestamp=predictions_data.get("prediction_timestamp"),
                overall_confidence=predictions_data.get("overall_confidence", 0.0),
                predictions=predictions_data.get("predictions", []),
                document_classification=predictions_data.get("document_classification"),
                entities=predictions_data.get("entities", []),
                key_phrases=predictions_data.get("key_phrases", []),
                risk_indicators=predictions_data.get("risk_indicators", [])
            )
    
    def _configure_correction_endpoints(self) -> None:
        """Configure human correction endpoints."""
        
        @self._router.post("/{document_id}/correct", response_model=DocumentResponse)
        async def apply_correction(
            *,
            db: Session = Depends(get_db),
            document_id: int = Path(..., description="Document ID"),
            correction_data: DocumentCorrection,
            current_user: User = Depends(get_current_user),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:correct"))
        ):
            """Apply human corrections to a document."""
            try:
                document = DocumentService.apply_correction(
                    db=db,
                    document_id=document_id,
                    correction_data=correction_data,
                    organization_id=organization.id,
                    corrected_by_id=current_user.id
                )
                return DocumentResponse.from_orm(document)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self._router.get("/{document_id}/corrections")
        async def get_corrections(
            *,
            db: Session = Depends(get_db),
            document_id: int = Path(..., description="Document ID"),
            limit: int = Query(10, ge=1, le=100, description="Maximum number of corrections to return"),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:read"))
        ):
            """Get correction history for a document."""
            from models.document import DocumentCorrection as CorrectionModel
            
            document = DocumentService.get_document(db, document_id, organization.id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            corrections = db.query(CorrectionModel).filter(
                CorrectionModel.document_id == document_id
            ).order_by(CorrectionModel.created_at.desc()).limit(limit).all()
            
            return {
                "document_id": document_id,
                "corrections": [
                    {
                        "id": c.id,
                        "field_path": c.field_path,
                        "correction_type": c.correction_type,
                        "original_value": c.original_value,
                        "corrected_value": c.corrected_value,
                        "confidence_before": c.confidence_before,
                        "confidence_after": c.confidence_after,
                        "correction_reason": c.correction_reason,
                        "corrected_by": c.corrected_by.full_name if c.corrected_by else None,
                        "review_status": c.review_status,
                        "created_at": c.created_at
                    } for c in corrections
                ]
            }
    
    def _configure_audit_endpoints(self) -> None:
        """Configure audit and version control endpoints."""
        
        @self._router.get("/{document_id}/audit", response_model=Dict[str, Any])
        async def get_audit_trail(
            *,
            db: Session = Depends(get_db),
            document_id: int = Path(..., description="Document ID"),
            limit: int = Query(50, ge=1, le=100, description="Maximum number of audit records to return"),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:audit"))
        ):
            """Get audit trail for a document."""
            try:
                audit_trail = DocumentService.get_audit_trail(
                    db=db,
                    document_id=document_id,
                    organization_id=organization.id,
                    limit=limit
                )
                return audit_trail
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self._router.get("/{document_id}/versions")
        async def get_document_versions(
            *,
            db: Session = Depends(get_db),
            document_id: int = Path(..., description="Document ID"),
            limit: int = Query(10, ge=1, le=50, description="Maximum number of versions to return"),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:read"))
        ):
            """Get version history for a document."""
            from models.document import DocumentVersion
            
            document = DocumentService.get_document(db, document_id, organization.id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            versions = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(DocumentVersion.created_at.desc()).limit(limit).all()
            
            return {
                "document_id": document_id,
                "current_version": document.version,
                "versions": [
                    {
                        "version_number": v.version_number,
                        "title": v.title,
                        "change_summary": v.change_summary,
                        "change_reason": v.change_reason,
                        "changed_by": v.changed_by.full_name if v.changed_by else None,
                        "created_at": v.created_at,
                        "prediction_status": v.prediction_status,
                        "prediction_score": v.prediction_score
                    } for v in versions
                ]
            }
    
    def _configure_search_endpoints(self) -> None:
        """Configure search and analytics endpoints."""
        
        @self._router.get("/stats/overview", response_model=DocumentStats)
        async def get_document_stats(
            *,
            db: Session = Depends(get_db),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:read"))
        ):
            """Get document statistics for the organization."""
            return DocumentService.get_document_stats(db, organization.id)

        @self._router.get("/search/quick", response_model=List[DocumentSearchResponse])
        async def quick_search_documents(
            *,
            db: Session = Depends(get_db),
            q: str = Query(..., min_length=2, description="Search term"),
            limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:read"))
        ):
            """Quick search documents for typeahead/autocomplete."""
            documents = DocumentService.search_documents(
                db=db,
                organization_id=organization.id,
                search_term=q,
                limit=limit
            )
            
            return [
                DocumentSearchResponse(
                    id=doc.id,
                    title=doc.title,
                    document_type=doc.document_type,
                    status=doc.status,
                    prediction_score=doc.prediction_score,
                    case_title=doc.case.title if doc.case else None,
                    client_name=doc.client.name if doc.client else None
                ) for doc in documents
            ]
    
    def _configure_bulk_operations(self) -> None:
        """Configure bulk operation endpoints."""
        
        @self._router.post("/bulk", response_model=DocumentBulkResult)
        async def bulk_update_documents(
            *,
            db: Session = Depends(get_db),
            bulk_action: DocumentBulkAction,
            current_user: User = Depends(get_current_user),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:bulk_update"))
        ):
            """Perform bulk operations on documents."""
            try:
                result = DocumentService.bulk_update_documents(
                    db=db,
                    bulk_action=bulk_action,
                    organization_id=organization.id,
                    updated_by_id=current_user.id
                )
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
    
    def _configure_sharing_endpoints(self) -> None:
        """Configure document sharing and permission endpoints."""
        
        @self._router.post("/{document_id}/share")
        async def share_document(
            *,
            db: Session = Depends(get_db),
            document_id: int = Path(..., description="Document ID"),
            share_data: Dict[str, Any] = Body(...),
            current_user: User = Depends(get_current_user),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:share"))
        ):
            """Share a document with other users."""
            from models.document import DocumentShare
            
            document = DocumentService.get_document(db, document_id, organization.id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Validate shared_with_id exists and belongs to organization
            shared_with_id = share_data.get("shared_with_id")
            if not shared_with_id:
                raise HTTPException(status_code=400, detail="shared_with_id is required")
            
            shared_user = db.query(User).filter(
                User.id == shared_with_id,
                User.organization_id == organization.id,
                User.is_deleted == False
            ).first()
            
            if not shared_user:
                raise HTTPException(status_code=400, detail="User not found in organization")
            
            # Check if already shared
            existing_share = db.query(DocumentShare).filter(
                DocumentShare.document_id == document_id,
                DocumentShare.shared_with_id == shared_with_id
            ).first()
            
            if existing_share:
                raise HTTPException(status_code=400, detail="Document already shared with this user")
            
            # Create share
            share = DocumentShare(
                document_id=document_id,
                shared_by_id=current_user.id,
                shared_with_id=shared_with_id,
                permission_level=share_data.get("permission_level", "read"),
                expires_at=share_data.get("expires_at")
            )
            
            db.add(share)
            db.commit()
            
            return {
                "message": "Document shared successfully",
                "share_id": share.id,
                "shared_with": shared_user.full_name,
                "permission_level": share.permission_level
            }

        @self._router.delete("/{document_id}/share/{share_id}")
        async def revoke_document_share(
            *,
            db: Session = Depends(get_db),
            document_id: int = Path(..., description="Document ID"),
            share_id: int = Path(..., description="Share ID"),
            current_user: User = Depends(get_current_user),
            organization: Organization = Depends(get_current_organization),
            _: None = Depends(require_permission("document:share"))
        ):
            """Revoke document share access."""
            from models.document import DocumentShare
            
            document = DocumentService.get_document(db, document_id, organization.id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            share = db.query(DocumentShare).filter(
                DocumentShare.id == share_id,
                DocumentShare.document_id == document_id
            ).first()
            
            if not share:
                raise HTTPException(status_code=404, detail="Share not found")
            
            # Only the original sharer or document owner can revoke
            if share.shared_by_id != current_user.id and document.created_by_id != current_user.id:
                raise HTTPException(status_code=403, detail="Permission denied")
            
            db.delete(share)
            db.commit()
            
            return {"message": "Document share revoked successfully"}

        @self._router.get("/{document_id}/permissions", response_model=DocumentPermissionCheck)
        async def check_document_permissions(
            *,
            db: Session = Depends(get_db),
            document_id: int = Path(..., description="Document ID"),
            current_user: User = Depends(get_current_user),
            organization: Organization = Depends(get_current_organization)
        ):
            """Check current user's permissions for a document."""
            document = DocumentService.get_document(db, document_id, organization.id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Basic permissions based on ownership
            can_read = True  # If they can access the endpoint, they can read
            can_update = document.created_by_id == current_user.id
            can_delete = document.created_by_id == current_user.id
            can_share = document.created_by_id == current_user.id
            can_correct = True  # Basic correction permission
            can_predict = True  # Basic prediction permission
            
            # Check for role-based permissions (would integrate with your RBAC system)
            # This is a simplified version - you'd want to check actual user roles/permissions
            
            return DocumentPermissionCheck(
                can_read=can_read,
                can_update=can_update,
                can_delete=can_delete,
                can_share=can_share,
                can_correct=can_correct,
                can_predict=can_predict,
                is_owner=document.created_by_id == current_user.id
            )


# Initialize the router
document_router = DocumentRouter()
