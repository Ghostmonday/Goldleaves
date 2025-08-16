# tests/test_document_prediction.py

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from models.document import (
    Document, DocumentVersion, DocumentCorrection, DocumentShare,
    PredictionStatus, DocumentType, DocumentStatus, DocumentConfidentiality
)
from models.user import User, Organization
from models.case import Case
from models.client import Client
from services.document import DocumentService
from schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentFilter,
    DocumentPrediction, PredictionField, PredictionIngest,
    DocumentCorrection as CorrectionSchema, FieldCorrection,
    CorrectionType, DocumentBulkAction
)


class TestDocumentPredictionModels:
    """Test document prediction data models."""

    def test_document_creation_with_predictions(self, db_session: Session, test_organization: Organization, test_user: User):
        """Test creating a document with AI predictions."""
        prediction_data = {
            "model_name": "legal-classifier-v2",
            "model_version": "2.1.0",
            "overall_confidence": 0.87,
            "predictions": [
                {
                    "field_name": "document_type",
                    "predicted_value": "contract",
                    "confidence": 0.92,
                    "alternatives": ["agreement", "legal_document"]
                }
            ]
        }

        document = Document(
            title="Test Contract",
            document_type=DocumentType.CONTRACT,
            status=DocumentStatus.DRAFT,
            confidentiality=DocumentConfidentiality.INTERNAL,
            ai_predictions=prediction_data,
            prediction_score=0.87,
            prediction_status=PredictionStatus.PENDING,
            organization_id=test_organization.id,
            created_by_id=test_user.id
        )

        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)

        assert document.id is not None
        assert document.ai_predictions == prediction_data
        assert document.prediction_score == 0.87
        assert document.prediction_status == PredictionStatus.PENDING
        assert document.get_prediction_confidence() == 0.87

    def test_document_version_tracking(self, db_session: Session, test_organization: Organization, test_user: User):
        """Test document version tracking for predictions."""
        document = Document(
            title="Version Test Document",
            document_type=DocumentType.LEGAL_BRIEF,
            status=DocumentStatus.DRAFT,
            confidentiality=DocumentConfidentiality.CONFIDENTIAL,
            organization_id=test_organization.id,
            created_by_id=test_user.id,
            version=1
        )

        db_session.add(document)
        db_session.commit()

        # Create version snapshot
        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            title=document.title,
            content=document.content,
            ai_predictions={"test": "data"},
            prediction_status=PredictionStatus.PENDING,
            prediction_score=0.75,
            change_summary="Initial version",
            change_reason="Document creation",
            changed_by_id=test_user.id
        )

        db_session.add(version)
        db_session.commit()

        assert version.id is not None
        assert version.prediction_status == PredictionStatus.PENDING
        assert version.prediction_score == 0.75

    def test_document_correction_tracking(self, db_session: Session, test_organization: Organization, test_user: User):
        """Test document correction tracking."""
        document = Document(
            title="Correction Test Document",
            document_type=DocumentType.CONTRACT,
            status=DocumentStatus.DRAFT,
            confidentiality=DocumentConfidentiality.INTERNAL,
            organization_id=test_organization.id,
            created_by_id=test_user.id
        )

        db_session.add(document)
        db_session.commit()

        # Create correction
        correction = DocumentCorrection(
            document_id=document.id,
            field_path="contract.parties.0.name",
            original_value="Acme Corp",
            corrected_value="ACME Corporation",
            confidence_before=0.85,
            confidence_after=1.0,
            correction_reason="Human verification",
            correction_type="edit",
            corrected_by_id=test_user.id,
            review_status="approved"
        )

        db_session.add(correction)
        db_session.commit()

        assert correction.id is not None
        assert correction.field_path == "contract.parties.0.name"
        assert correction.confidence_after == 1.0
        assert correction.review_status == "approved"


class TestDocumentService:
    """Test document service layer with prediction functionality."""

    def test_create_document_with_case_client(self, db_session: Session, test_organization: Organization, test_user: User):
        """Test creating document with case and client relationships."""
        # Create test case and client
        client = Client(
            name="Test Client Corp",
            type="corporate",
            organization_id=test_organization.id,
            created_by_id=test_user.id
        )
        db_session.add(client)
        db_session.commit()

        case = Case(
            title="Test Legal Case",
            description="A test case for document management",
            status="active",
            client_id=client.id,
            organization_id=test_organization.id,
            created_by_id=test_user.id
        )
        db_session.add(case)
        db_session.commit()

        # Create document
        document_data = DocumentCreate(
            title="Case Document",
            document_type=DocumentType.LEGAL_BRIEF,
            status=DocumentStatus.DRAFT,
            confidentiality=DocumentConfidentiality.CONFIDENTIAL,
            case_id=case.id,
            client_id=client.id,
            content="Test document content for the case"
        )

        document = DocumentService.create_document(
            db=db_session,
            document_data=document_data,
            organization_id=test_organization.id,
            created_by_id=test_user.id
        )

        assert document.id is not None
        assert document.case_id == case.id
        assert document.client_id == client.id
        assert document.version == 1

    def test_ingest_prediction_data(self, db_session: Session, test_organization: Organization, test_user: User):
        """Test ingesting AI prediction data."""
        # Create document
        document_data = DocumentCreate(
            title="Prediction Test Document",
            document_type=DocumentType.CONTRACT,
            status=DocumentStatus.DRAFT,
            confidentiality=DocumentConfidentiality.INTERNAL,
            content="This is a test contract for AI analysis"
        )

        document = DocumentService.create_document(
            db=db_session,
            document_data=document_data,
            organization_id=test_organization.id,
            created_by_id=test_user.id
        )

        # Create prediction data
        prediction_fields = [
            PredictionField(
                field_name="contract_type",
                predicted_value="service_agreement",
                confidence=0.89,
                field_type="classification",
                alternatives=["consulting_agreement", "license_agreement"]
            ),
            PredictionField(
                field_name="parties.0.name",
                predicted_value="ACME Corporation",
                confidence=0.95,
                field_type="entity_extraction",
                original_text="ACME Corp"
            )
        ]

        document_prediction = DocumentPrediction(
            model_name="legal-analyzer-v3",
            model_version="3.2.1",
            prediction_timestamp=datetime.utcnow(),
            overall_confidence=0.92,
            predictions=prediction_fields,
            document_classification="contract",
            entities=["ACME Corporation", "Service Agreement"],
            key_phrases=["payment terms", "termination clause"],
            risk_indicators=["auto-renewal clause", "liability limitation"]
        )

        prediction_ingest = PredictionIngest(
            prediction_data=document_prediction,
            auto_apply_high_confidence=False,
            validation_required=True
        )

        # Ingest predictions
        updated_document = DocumentService.ingest_prediction(
            db=db_session,
            document_id=document.id,
            prediction_ingest=prediction_ingest,
            organization_id=test_organization.id,
            ingested_by_id=test_user.id
        )

        assert updated_document.prediction_score == 0.92
        assert updated_document.prediction_status == PredictionStatus.PENDING
        assert updated_document.ai_predictions is not None
        assert updated_document.ai_predictions["model_name"] == "legal-analyzer-v3"
        assert updated_document.version == 2  # Version incremented

    def test_apply_corrections(self, db_session: Session, test_organization: Organization, test_user: User):
        """Test applying human corrections to predictions."""
        # Create document with predictions
        document_data = DocumentCreate(
            title="Correction Test Document",
            document_type=DocumentType.CONTRACT,
            status=DocumentStatus.DRAFT,
            confidentiality=DocumentConfidentiality.INTERNAL,
            ai_predictions={"test": "initial_predictions"},
            prediction_score=0.75,
            prediction_status=PredictionStatus.PENDING
        )

        document = DocumentService.create_document(
            db=db_session,
            document_data=document_data,
            organization_id=test_organization.id,
            created_by_id=test_user.id
        )

        # Create corrections
        field_corrections = [
            FieldCorrection(
                field_path="contract_type",
                original_value="service_agreement",
                corrected_value="consulting_agreement",
                confidence_before=0.75,
                confidence_after=1.0,
                correction_type=CorrectionType.EDIT
            ),
            FieldCorrection(
                field_path="parties.0.name",
                original_value="ACME Corp",
                corrected_value="ACME Corporation",
                confidence_before=0.80,
                confidence_after=1.0,
                correction_type=CorrectionType.CONFIRM
            )
        ]

        correction_data = CorrectionSchema(
            corrections=field_corrections,
            correction_reason="Human review and verification",
            requires_review=False
        )

        # Apply corrections
        corrected_document = DocumentService.apply_correction(
            db=db_session,
            document_id=document.id,
            correction_data=correction_data,
            organization_id=test_organization.id,
            corrected_by_id=test_user.id
        )

        assert corrected_document.prediction_status == PredictionStatus.PARTIALLY_CONFIRMED
        assert corrected_document.corrections is not None
        assert corrected_document.version == 2  # Version incremented

        # Check correction records were created
        corrections = db_session.query(DocumentCorrection).filter(
            DocumentCorrection.document_id == document.id
        ).all()
        assert len(corrections) == 2

    def test_document_filtering(self, db_session: Session, test_organization: Organization, test_user: User):
        """Test document filtering functionality."""
        # Create multiple documents with different properties
        documents_data = [
            DocumentCreate(
                title="High Confidence Contract",
                document_type=DocumentType.CONTRACT,
                status=DocumentStatus.FINAL,
                confidentiality=DocumentConfidentiality.CONFIDENTIAL,
                prediction_score=0.95,
                prediction_status=PredictionStatus.CONFIRMED,
                tags=["high-priority", "contract"]
            ),
            DocumentCreate(
                title="Low Confidence Brief",
                document_type=DocumentType.LEGAL_BRIEF,
                status=DocumentStatus.DRAFT,
                confidentiality=DocumentConfidentiality.INTERNAL,
                prediction_score=0.65,
                prediction_status=PredictionStatus.PENDING,
                tags=["review-needed"]
            ),
            DocumentCreate(
                title="Medium Confidence Agreement",
                document_type=DocumentType.AGREEMENT,
                status=DocumentStatus.REVIEW,
                confidentiality=DocumentConfidentiality.PUBLIC,
                prediction_score=0.82,
                prediction_status=PredictionStatus.PARTIALLY_CONFIRMED,
                tags=["standard", "agreement"]
            )
        ]

        created_docs = []
        for doc_data in documents_data:
            doc = DocumentService.create_document(
                db=db_session,
                document_data=doc_data,
                organization_id=test_organization.id,
                created_by_id=test_user.id
            )
            created_docs.append(doc)

        # Test filtering by prediction score
        high_confidence_filter = DocumentFilter(
            min_prediction_score=0.9
        )
        docs, total = DocumentService.list_documents(
            db=db_session,
            organization_id=test_organization.id,
            filters=high_confidence_filter
        )
        assert total == 1
        assert docs[0].title == "High Confidence Contract"

        # Test filtering by prediction status
        pending_filter = DocumentFilter(
            prediction_status=PredictionStatus.PENDING
        )
        docs, total = DocumentService.list_documents(
            db=db_session,
            organization_id=test_organization.id,
            filters=pending_filter
        )
        assert total == 1
        assert docs[0].title == "Low Confidence Brief"

        # Test filtering by tags
        contract_filter = DocumentFilter(
            tags=["contract"]
        )
        docs, total = DocumentService.list_documents(
            db=db_session,
            organization_id=test_organization.id,
            filters=contract_filter
        )
        assert total == 1
        assert docs[0].title == "High Confidence Contract"

    def test_audit_trail(self, db_session: Session, test_organization: Organization, test_user: User):
        """Test audit trail functionality."""
        # Create document
        document_data = DocumentCreate(
            title="Audit Trail Test",
            document_type=DocumentType.CONTRACT,
            status=DocumentStatus.DRAFT,
            confidentiality=DocumentConfidentiality.INTERNAL
        )

        document = DocumentService.create_document(
            db=db_session,
            document_data=document_data,
            organization_id=test_organization.id,
            created_by_id=test_user.id
        )

        # Update document
        update_data = DocumentUpdate(
            title="Updated Audit Trail Test",
            status=DocumentStatus.REVIEW
        )

        DocumentService.update_document(
            db=db_session,
            document_id=document.id,
            document_update=update_data,
            organization_id=test_organization.id,
            updated_by_id=test_user.id
        )

        # Get audit trail
        audit_trail = DocumentService.get_audit_trail(
            db=db_session,
            document_id=document.id,
            organization_id=test_organization.id
        )

        assert audit_trail["document_id"] == document.id
        assert audit_trail["current_version"] == 2
        assert len(audit_trail["recent_versions"]) >= 1

    def test_bulk_operations(self, db_session: Session, test_organization: Organization, test_user: User):
        """Test bulk document operations."""
        # Create multiple documents
        document_ids = []
        for i in range(3):
            document_data = DocumentCreate(
                title=f"Bulk Test Document {i+1}",
                document_type=DocumentType.CONTRACT,
                status=DocumentStatus.DRAFT,
                confidentiality=DocumentConfidentiality.INTERNAL
            )

            document = DocumentService.create_document(
                db=db_session,
                document_data=document_data,
                organization_id=test_organization.id,
                created_by_id=test_user.id
            )
            document_ids.append(document.id)

        # Perform bulk status update
        bulk_action = DocumentBulkAction(
            document_ids=document_ids,
            action="update_status",
            parameters={"status": "review"}
        )

        result = DocumentService.bulk_update_documents(
            db=db_session,
            bulk_action=bulk_action,
            organization_id=test_organization.id,
            updated_by_id=test_user.id
        )

        assert result.success_count == 3
        assert result.error_count == 0
        assert len(result.updated_documents) == 3

        # Verify documents were updated
        for doc_id in document_ids:
            document = DocumentService.get_document(db_session, doc_id, test_organization.id)
            assert document.status == DocumentStatus.REVIEW


class TestDocumentAPI:
    """Test document prediction API endpoints."""

    def test_create_document_endpoint(self, client: TestClient, test_user_token: str, test_organization: Organization):
        """Test document creation endpoint."""
        document_data = {
            "title": "API Test Document",
            "document_type": "contract",
            "status": "draft",
            "confidentiality": "internal",
            "content": "Test document content"
        }

        response = client.post(
            "/documents/",
            json=document_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "API Test Document"
        assert data["document_type"] == "contract"

    def test_ingest_prediction_endpoint(self, client: TestClient, test_user_token: str, test_document_id: int):
        """Test prediction ingestion endpoint."""
        prediction_data = {
            "prediction_data": {
                "model_name": "legal-classifier-v2",
                "model_version": "2.1.0",
                "prediction_timestamp": datetime.utcnow().isoformat(),
                "overall_confidence": 0.89,
                "predictions": [
                    {
                        "field_name": "document_type",
                        "predicted_value": "contract",
                        "confidence": 0.92,
                        "field_type": "classification",
                        "alternatives": ["agreement"]
                    }
                ],
                "document_classification": "contract",
                "entities": ["ACME Corp"],
                "key_phrases": ["payment terms"],
                "risk_indicators": ["liability clause"]
            },
            "auto_apply_high_confidence": False,
            "validation_required": True
        }

        response = client.post(
            f"/documents/{test_document_id}/predict",
            json=prediction_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["prediction_score"] == 0.89
        assert data["prediction_status"] == "pending"

    def test_apply_correction_endpoint(self, client: TestClient, test_user_token: str, test_document_id: int):
        """Test correction application endpoint."""
        correction_data = {
            "corrections": [
                {
                    "field_path": "contract_type",
                    "original_value": "service_agreement",
                    "corrected_value": "consulting_agreement",
                    "confidence_before": 0.75,
                    "confidence_after": 1.0,
                    "correction_type": "edit"
                }
            ],
            "correction_reason": "Human verification",
            "requires_review": False
        }

        response = client.post(
            f"/documents/{test_document_id}/correct",
            json=correction_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "corrections" in data

    def test_document_permissions(self, client: TestClient, test_user_token: str, test_document_id: int):
        """Test document permission checking."""
        response = client.get(
            f"/documents/{test_document_id}/permissions",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "can_read" in data
        assert "can_update" in data
        assert "can_correct" in data
        assert "can_predict" in data


class TestDocumentIntegration:
    """Integration tests for the complete document prediction workflow."""

    def test_complete_prediction_workflow(self, db_session: Session, test_organization: Organization, test_user: User):
        """Test the complete workflow from document creation to correction."""

        # Step 1: Create document
        document_data = DocumentCreate(
            title="Integration Test Contract",
            document_type=DocumentType.CONTRACT,
            status=DocumentStatus.DRAFT,
            confidentiality=DocumentConfidentiality.CONFIDENTIAL,
            content="This is a service agreement between parties..."
        )

        document = DocumentService.create_document(
            db=db_session,
            document_data=document_data,
            organization_id=test_organization.id,
            created_by_id=test_user.id
        )

        assert document.version == 1
        initial_version = document.version

        # Step 2: Ingest AI predictions
        prediction_fields = [
            PredictionField(
                field_name="contract_type",
                predicted_value="service_agreement",
                confidence=0.87,
                field_type="classification"
            ),
            PredictionField(
                field_name="effective_date",
                predicted_value="2024-01-15",
                confidence=0.92,
                field_type="date_extraction"
            )
        ]

        document_prediction = DocumentPrediction(
            model_name="legal-analyzer-v3",
            model_version="3.2.1",
            prediction_timestamp=datetime.utcnow(),
            overall_confidence=0.895,
            predictions=prediction_fields,
            document_classification="contract"
        )

        prediction_ingest = PredictionIngest(
            prediction_data=document_prediction,
            auto_apply_high_confidence=False
        )

        predicted_document = DocumentService.ingest_prediction(
            db=db_session,
            document_id=document.id,
            prediction_ingest=prediction_ingest,
            organization_id=test_organization.id,
            ingested_by_id=test_user.id
        )

        assert predicted_document.prediction_status == PredictionStatus.PENDING
        assert predicted_document.prediction_score == 0.895
        assert predicted_document.version == initial_version + 1

        # Step 3: Apply human corrections
        field_corrections = [
            FieldCorrection(
                field_path="contract_type",
                original_value="service_agreement",
                corrected_value="consulting_agreement",
                confidence_before=0.87,
                confidence_after=1.0,
                correction_type=CorrectionType.EDIT
            ),
            FieldCorrection(
                field_path="effective_date",
                original_value="2024-01-15",
                corrected_value="2024-01-15",
                confidence_before=0.92,
                confidence_after=1.0,
                correction_type=CorrectionType.CONFIRM
            )
        ]

        correction_data = CorrectionSchema(
            corrections=field_corrections,
            correction_reason="Human review completed"
        )

        corrected_document = DocumentService.apply_correction(
            db=db_session,
            document_id=document.id,
            correction_data=correction_data,
            organization_id=test_organization.id,
            corrected_by_id=test_user.id
        )

        assert corrected_document.prediction_status == PredictionStatus.PARTIALLY_CONFIRMED
        assert corrected_document.version == initial_version + 2

        # Step 4: Verify audit trail
        audit_trail = DocumentService.get_audit_trail(
            db=db_session,
            document_id=document.id,
            organization_id=test_organization.id
        )

        assert audit_trail["current_version"] == initial_version + 2
        assert len(audit_trail["recent_versions"]) >= 2
        assert len(audit_trail["recent_corrections"]) >= 2

        # Step 5: Verify correction records
        corrections = db_session.query(DocumentCorrection).filter(
            DocumentCorrection.document_id == document.id
        ).all()

        assert len(corrections) == 2
        assert any(c.correction_type == "edit" for c in corrections)
        assert any(c.correction_type == "confirm" for c in corrections)


# Fixtures for testing
@pytest.fixture
def test_document_id(db_session: Session, test_organization: Organization, test_user: User) -> int:
    """Create a test document and return its ID."""
    document_data = DocumentCreate(
        title="Test Document for API",
        document_type=DocumentType.CONTRACT,
        status=DocumentStatus.DRAFT,
        confidentiality=DocumentConfidentiality.INTERNAL
    )

    document = DocumentService.create_document(
        db=db_session,
        document_data=document_data,
        organization_id=test_organization.id,
        created_by_id=test_user.id
    )

    return document.id
