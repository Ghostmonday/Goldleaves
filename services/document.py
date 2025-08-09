# services/document.py

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta

from models.document import (
    Document, DocumentVersion, DocumentCorrection, PredictionStatus,
    DocumentType, DocumentStatus, DocumentConfidentiality
)
from models.case import Case
from models.client import Client
from schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentFilter, DocumentStats,
    PredictionIngest, DocumentCorrection as CorrectionSchema, DocumentBulkAction,
    DocumentBulkResult
)
from core.exceptions import NotFoundError, ValidationError


class DocumentService:
    """Service layer for document management with AI prediction support."""
    
    @staticmethod
    def create_document(
        db: Session,
        document_data: DocumentCreate,
        organization_id: int,
        created_by_id: int
    ) -> Document:
        """Create a new document with optional AI predictions."""
        
        # Validate relationships exist and belong to organization
        if document_data.case_id:
            case = db.query(Case).filter(
                and_(
                    Case.id == document_data.case_id,
                    Case.organization_id == organization_id,
                    Case.is_deleted == False
                )
            ).first()
            if not case:
                raise ValidationError("Case not found or does not belong to organization")
        
        if document_data.client_id:
            client = db.query(Client).filter(
                and_(
                    Client.id == document_data.client_id,
                    Client.organization_id == organization_id,
                    Client.is_deleted == False
                )
            ).first()
            if not client:
                raise ValidationError("Client not found or does not belong to organization")
        
        # Create document
        document = Document(
            title=document_data.title,
            description=document_data.description,
            document_type=document_data.document_type,
            status=document_data.status,
            confidentiality=document_data.confidentiality,
            
            # File information
            file_name=document_data.file_name,
            file_path=document_data.file_path,
            file_size=document_data.file_size,
            mime_type=document_data.mime_type,
            file_hash=document_data.file_hash,
            
            # Content
            content=document_data.content,
            metadata=document_data.metadata,
            
            # AI predictions
            ai_predictions=document_data.ai_predictions,
            prediction_score=document_data.prediction_score,
            prediction_status=PredictionStatus.PENDING if document_data.ai_predictions else PredictionStatus.PENDING,
            
            # Relationships
            case_id=document_data.case_id,
            client_id=document_data.client_id,
            organization_id=organization_id,
            created_by_id=created_by_id,
            
            # Metadata
            tags=document_data.tags or [],
            legal_hold=document_data.legal_hold,
            retention_date=document_data.retention_date
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Create initial version
        DocumentService._create_version_snapshot(
            db, document, created_by_id, "Initial document creation", "Document created"
        )
        
        return document
    
    @staticmethod
    def get_document(db: Session, document_id: int, organization_id: int) -> Optional[Document]:
        """Get a document by ID with organization isolation."""
        return db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.organization_id == organization_id,
                Document.is_deleted == False
            )
        ).first()
    
    @staticmethod
    def update_document(
        db: Session,
        document_id: int,
        document_update: DocumentUpdate,
        organization_id: int,
        updated_by_id: int
    ) -> Optional[Document]:
        """Update a document with version tracking."""
        document = DocumentService.get_document(db, document_id, organization_id)
        if not document:
            raise NotFoundError("Document not found")
        
        # Track changes for version history
        changes = []
        update_data = document_update.dict(exclude_unset=True)
        
        for field, new_value in update_data.items():
            old_value = getattr(document, field)
            if old_value != new_value:
                changes.append(f"{field}: {old_value} → {new_value}")
                setattr(document, field, new_value)
        
        if changes:
            # Increment version
            document.increment_version(updated_by_id)
            
            db.commit()
            db.refresh(document)
            
            # Create version snapshot
            DocumentService._create_version_snapshot(
                db, document, updated_by_id, 
                f"Document updated: {', '.join(changes[:3])}", 
                "Manual update"
            )
        
        return document
    
    @staticmethod
    def delete_document(db: Session, document_id: int, organization_id: int) -> bool:
        """Soft delete a document with organization isolation."""
        document = DocumentService.get_document(db, document_id, organization_id)
        if not document:
            raise NotFoundError("Document not found")
        
        document.soft_delete()
        db.commit()
        
        return True
    
    @staticmethod
    def list_documents(
        db: Session,
        organization_id: int,
        filters: Optional[DocumentFilter] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> Tuple[List[Document], int]:
        """List documents with filtering, pagination, and organization isolation."""
        
        query = db.query(Document).filter(
            and_(
                Document.organization_id == organization_id,
                Document.is_deleted == False
            )
        )
        
        # Apply filters
        if filters:
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Document.title.ilike(search_term),
                        Document.content.ilike(search_term),
                        Document.description.ilike(search_term)
                    )
                )
            
            if filters.document_type:
                query = query.filter(Document.document_type == filters.document_type)
            
            if filters.status:
                query = query.filter(Document.status == filters.status)
            
            if filters.confidentiality:
                query = query.filter(Document.confidentiality == filters.confidentiality)
            
            if filters.prediction_status:
                query = query.filter(Document.prediction_status == filters.prediction_status)
            
            if filters.case_id:
                query = query.filter(Document.case_id == filters.case_id)
            
            if filters.client_id:
                query = query.filter(Document.client_id == filters.client_id)
            
            if filters.created_by_id:
                query = query.filter(Document.created_by_id == filters.created_by_id)
            
            if filters.tags:
                for tag in filters.tags:
                    query = query.filter(Document.tags.contains([tag]))
            
            if filters.legal_hold is not None:
                query = query.filter(Document.legal_hold == filters.legal_hold)
            
            if filters.min_prediction_score is not None:
                query = query.filter(Document.prediction_score >= filters.min_prediction_score)
            
            if filters.max_prediction_score is not None:
                query = query.filter(Document.prediction_score <= filters.max_prediction_score)
            
            if filters.created_after:
                query = query.filter(Document.created_at >= filters.created_after)
            
            if filters.created_before:
                query = query.filter(Document.created_at <= filters.created_before)
            
            if filters.has_content is not None:
                if filters.has_content:
                    query = query.filter(Document.content.isnot(None))
                else:
                    query = query.filter(Document.content.is_(None))
            
            if filters.has_predictions is not None:
                if filters.has_predictions:
                    query = query.filter(Document.ai_predictions != {})
                else:
                    query = query.filter(Document.ai_predictions == {})
            
            if filters.needs_review:
                query = query.filter(Document.prediction_status == PredictionStatus.PENDING)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply ordering
        if order_direction.lower() == "desc":
            query = query.order_by(desc(getattr(Document, order_by, Document.created_at)))
        else:
            query = query.order_by(asc(getattr(Document, order_by, Document.created_at)))
        
        # Apply pagination with eager loading
        documents = query.options(
            joinedload(Document.case),
            joinedload(Document.client),
            joinedload(Document.created_by)
        ).offset(skip).limit(limit).all()
        
        return documents, total
    
    @staticmethod
    def ingest_prediction(
        db: Session,
        document_id: int,
        prediction_ingest: PredictionIngest,
        organization_id: int,
        ingested_by_id: int
    ) -> Document:
        """Ingest AI prediction data into a document."""
        document = DocumentService.get_document(db, document_id, organization_id)
        if not document:
            raise NotFoundError("Document not found")
        
        prediction_data = prediction_ingest.prediction_data
        
        # Store prediction data
        document.ai_predictions = {
            "model_name": prediction_data.model_name,
            "model_version": prediction_data.model_version,
            "prediction_timestamp": prediction_data.prediction_timestamp.isoformat(),
            "overall_confidence": prediction_data.overall_confidence,
            "predictions": [pred.dict() for pred in prediction_data.predictions],
            "document_classification": prediction_data.document_classification,
            "entities": prediction_data.entities,
            "key_phrases": prediction_data.key_phrases,
            "risk_indicators": prediction_data.risk_indicators
        }
        
        document.prediction_score = prediction_data.overall_confidence
        
        # Auto-apply high confidence predictions if requested
        if prediction_ingest.auto_apply_high_confidence and prediction_data.overall_confidence >= 0.95:
            document.prediction_status = PredictionStatus.CONFIRMED
        else:
            document.prediction_status = PredictionStatus.PENDING
        
        # Increment version
        document.increment_version(ingested_by_id)
        
        db.commit()
        db.refresh(document)
        
        # Create version snapshot
        DocumentService._create_version_snapshot(
            db, document, ingested_by_id,
            f"AI predictions ingested (confidence: {prediction_data.overall_confidence:.2f})",
            "AI prediction ingestion"
        )
        
        return document
    
    @staticmethod
    def apply_correction(
        db: Session,
        document_id: int,
        correction_data: CorrectionSchema,
        organization_id: int,
        corrected_by_id: int
    ) -> Document:
        """Apply human corrections to a document."""
        document = DocumentService.get_document(db, document_id, organization_id)
        if not document:
            raise NotFoundError("Document not found")
        
        # Track corrections
        corrections_applied = []
        
        for field_correction in correction_data.corrections:
            # Create correction record
            correction_record = DocumentCorrection(
                document_id=document.id,
                field_path=field_correction.field_path,
                original_value=field_correction.original_value,
                corrected_value=field_correction.corrected_value,
                confidence_before=field_correction.confidence_before,
                confidence_after=field_correction.confidence_after,
                correction_reason=correction_data.correction_reason,
                correction_type=field_correction.correction_type.value,
                corrected_by_id=corrected_by_id,
                review_status="pending" if correction_data.requires_review else "approved"
            )
            
            db.add(correction_record)
            corrections_applied.append({
                "field_path": field_correction.field_path,
                "correction_type": field_correction.correction_type.value,
                "original_value": field_correction.original_value,
                "corrected_value": field_correction.corrected_value
            })
        
        # Update document correction tracking
        if document.corrections is None:
            document.corrections = {}
        
        document.corrections.update({
            "last_correction_timestamp": datetime.utcnow().isoformat(),
            "total_corrections": document.get_correction_count() + len(correction_data.corrections),
            "corrections_applied": corrections_applied
        })
        
        # Update prediction status based on corrections
        if all(c.correction_type.value == "confirm" for c in correction_data.corrections):
            document.prediction_status = PredictionStatus.CONFIRMED
        elif all(c.correction_type.value == "reject" for c in correction_data.corrections):
            document.prediction_status = PredictionStatus.REJECTED
        else:
            document.prediction_status = PredictionStatus.PARTIALLY_CONFIRMED
        
        # Increment version
        document.increment_version(corrected_by_id)
        
        db.commit()
        db.refresh(document)
        
        # Create version snapshot
        DocumentService._create_version_snapshot(
            db, document, corrected_by_id,
            f"Corrections applied to {len(correction_data.corrections)} fields",
            correction_data.correction_reason
        )
        
        return document
    
    @staticmethod
    def get_audit_trail(
        db: Session,
        document_id: int,
        organization_id: int,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get audit trail for a document."""
        document = DocumentService.get_document(db, document_id, organization_id)
        if not document:
            raise NotFoundError("Document not found")
        
        # Get recent versions
        versions = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(desc(DocumentVersion.created_at)).limit(10).all()
        
        # Get recent corrections
        corrections = db.query(DocumentCorrection).filter(
            DocumentCorrection.document_id == document_id
        ).order_by(desc(DocumentCorrection.created_at)).limit(10).all()
        
        return {
            "document_id": document_id,
            "current_version": document.version,
            "total_versions": len(document.versions) if document.versions else 0,
            "total_corrections": len(document.corrections_history) if document.corrections_history else 0,
            "last_modified": document.edited_at,
            "last_modified_by": document.edited_by.full_name if document.edited_by else None,
            "recent_versions": [
                {
                    "version": v.version_number,
                    "change_summary": v.change_summary,
                    "changed_by": v.changed_by.full_name if v.changed_by else None,
                    "created_at": v.created_at
                } for v in versions
            ],
            "recent_corrections": [
                {
                    "field_path": c.field_path,
                    "correction_type": c.correction_type,
                    "corrected_by": c.corrected_by.full_name if c.corrected_by else None,
                    "created_at": c.created_at,
                    "review_status": c.review_status
                } for c in corrections
            ]
        }
    
    @staticmethod
    def get_document_stats(db: Session, organization_id: int) -> DocumentStats:
        """Get document statistics for an organization."""
        
        base_query = db.query(Document).filter(
            and_(
                Document.organization_id == organization_id,
                Document.is_deleted == False
            )
        )
        
        total_documents = base_query.count()
        
        # Count by type
        by_type = {}
        for doc_type in DocumentType:
            count = base_query.filter(Document.document_type == doc_type).count()
            by_type[doc_type.value] = count
        
        # Count by status
        by_status = {}
        for status in DocumentStatus:
            count = base_query.filter(Document.status == status).count()
            by_status[status.value] = count
        
        # Count by prediction status
        by_prediction_status = {}
        for pred_status in PredictionStatus:
            count = base_query.filter(Document.prediction_status == pred_status).count()
            by_prediction_status[pred_status.value] = count
        
        # Prediction confidence metrics
        avg_score = base_query.with_entities(func.avg(Document.prediction_score)).scalar() or 0.0
        high_confidence = base_query.filter(Document.prediction_score >= 0.9).count()
        medium_confidence = base_query.filter(
            and_(Document.prediction_score >= 0.7, Document.prediction_score < 0.9)
        ).count()
        low_confidence = base_query.filter(Document.prediction_score < 0.7).count()
        
        # Correction metrics
        total_corrections = db.query(func.count(DocumentCorrection.id)).join(Document).filter(
            and_(
                Document.organization_id == organization_id,
                Document.is_deleted == False
            )
        ).scalar() or 0
        
        docs_with_corrections = base_query.join(DocumentCorrection).distinct().count()
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_documents = base_query.filter(Document.created_at >= thirty_days_ago).count()
        recent_corrections = db.query(func.count(DocumentCorrection.id)).join(Document).filter(
            and_(
                Document.organization_id == organization_id,
                Document.is_deleted == False,
                DocumentCorrection.created_at >= thirty_days_ago
            )
        ).scalar() or 0
        
        return DocumentStats(
            total_documents=total_documents,
            by_type=by_type,
            by_status=by_status,
            by_prediction_status=by_prediction_status,
            average_prediction_score=float(avg_score),
            high_confidence_count=high_confidence,
            medium_confidence_count=medium_confidence,
            low_confidence_count=low_confidence,
            total_corrections=total_corrections,
            documents_with_corrections=docs_with_corrections,
            documents_pending_review=by_prediction_status.get("pending", 0),
            recent_documents=recent_documents,
            recent_corrections=recent_corrections
        )
    
    @staticmethod
    def search_documents(
        db: Session,
        organization_id: int,
        search_term: str,
        limit: int = 10
    ) -> List[Document]:
        """Quick search for documents (for typeahead/autocomplete)."""
        
        search_pattern = f"%{search_term}%"
        
        return db.query(Document).filter(
            and_(
                Document.organization_id == organization_id,
                Document.is_deleted == False,
                or_(
                    Document.title.ilike(search_pattern),
                    Document.content.ilike(search_pattern),
                    Document.description.ilike(search_pattern)
                )
            )
        ).order_by(Document.title).limit(limit).all()
    
    @staticmethod
    def _create_version_snapshot(
        db: Session,
        document: Document,
        changed_by_id: int,
        change_summary: str,
        change_reason: str
    ):
        """Create a version snapshot for audit trail."""
        version = DocumentVersion(
            document_id=document.id,
            version_number=document.version,
            title=document.title,
            content=document.content,
            metadata=document.metadata,
            ai_predictions=document.ai_predictions,
            corrections=document.corrections,
            prediction_status=document.prediction_status,
            prediction_score=document.prediction_score,
            change_summary=change_summary,
            change_reason=change_reason,
            changed_by_id=changed_by_id
        )
        
        db.add(version)
        db.commit()
    
    @staticmethod
    def bulk_update_documents(
        db: Session,
        bulk_action: DocumentBulkAction,
        organization_id: int,
        updated_by_id: int
    ) -> DocumentBulkResult:
        """Perform bulk operations on documents."""
        
        result = DocumentBulkResult()
        
        for document_id in bulk_action.document_ids:
            try:
                document = DocumentService.get_document(db, document_id, organization_id)
                if not document:
                    result.error_count += 1
                    result.errors.append({
                        "document_id": document_id,
                        "error": "Document not found"
                    })
                    continue
                
                # Perform action
                if bulk_action.action == "update_status":
                    new_status = bulk_action.parameters.get("status")
                    if new_status and new_status in [s.value for s in DocumentStatus]:
                        document.status = DocumentStatus(new_status)
                        document.increment_version(updated_by_id)
                        result.success_count += 1
                        result.updated_documents.append(document_id)
                    else:
                        result.error_count += 1
                        result.errors.append({
                            "document_id": document_id,
                            "error": "Invalid status"
                        })
                
                elif bulk_action.action == "update_confidentiality":
                    new_confidentiality = bulk_action.parameters.get("confidentiality")
                    if new_confidentiality and new_confidentiality in [c.value for c in DocumentConfidentiality]:
                        document.confidentiality = DocumentConfidentiality(new_confidentiality)
                        document.increment_version(updated_by_id)
                        result.success_count += 1
                        result.updated_documents.append(document_id)
                    else:
                        result.error_count += 1
                        result.errors.append({
                            "document_id": document_id,
                            "error": "Invalid confidentiality level"
                        })
                
                elif bulk_action.action == "add_tags":
                    tags_to_add = bulk_action.parameters.get("tags", [])
                    for tag in tags_to_add:
                        document.add_tag(tag)
                    result.success_count += 1
                    result.updated_documents.append(document_id)
                
                elif bulk_action.action == "remove_tags":
                    tags_to_remove = bulk_action.parameters.get("tags", [])
                    for tag in tags_to_remove:
                        document.remove_tag(tag)
                    result.success_count += 1
                    result.updated_documents.append(document_id)
                
                elif bulk_action.action == "apply_legal_hold":
                    document.legal_hold = True
                    document.increment_version(updated_by_id)
                    result.success_count += 1
                    result.updated_documents.append(document_id)
                
                elif bulk_action.action == "remove_legal_hold":
                    document.legal_hold = False
                    document.increment_version(updated_by_id)
                    result.success_count += 1
                    result.updated_documents.append(document_id)
                
                else:
                    result.error_count += 1
                    result.errors.append({
                        "document_id": document_id,
                        "error": f"Unknown action: {bulk_action.action}"
                    })
                
            except Exception as e:
                result.error_count += 1
                result.errors.append({
                    "document_id": document_id,
                    "error": str(e)
                })
        
        if result.success_count > 0:
            db.commit()
        
        return result
