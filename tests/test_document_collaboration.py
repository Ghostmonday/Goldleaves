# tests/test_document_collaboration.py

"""Phase 6: Tests for document collaboration features including version control, diffing, and secure sharing."""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models.document import (
    Document, DocumentVersion, DocumentSecureShare, DocumentShareAccessLog,
    DocumentAuditEvent, DocumentVersionDiff, AuditEventType, SecureSharePermission,
    DocumentType, PredictionStatus
)
from models.user import User, Organization
from services.document_collaboration import DocumentCollaborationService
from schemas.document.collaboration import (
    VersionComparisonRequest, SecureShareCreate, ShareAccessRequest
)
from core.exceptions import NotFoundError, ValidationError, PermissionError

client = TestClient(app)


class TestDocumentCollaborationService:
    """Test the document collaboration service layer."""
    
    @pytest.fixture
    def sample_organization(self, db: Session) -> Organization:
        """Create a sample organization for testing."""
        org = Organization(
            name="Test Collaboration Org",
            domain="testcollab.com",
            is_active=True
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        return org
    
    @pytest.fixture
    def sample_user(self, db: Session, sample_organization: Organization) -> User:
        """Create a sample user for testing."""
        user = User(
            email="collab@testcollab.com",
            full_name="Collaboration Tester",
            hashed_password="hashed_password",
            is_active=True,
            organization_id=sample_organization.id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @pytest.fixture
    def sample_document_with_versions(self, db: Session, sample_user: User) -> Document:
        """Create a document with multiple versions for testing."""
        # Create base document
        document = Document(
            title="Collaboration Test Document",
            document_type=DocumentType.CONTRACT,
            file_path="/test/collab_doc.pdf",
            file_size=1024 * 1024,
            organization_id=sample_user.organization_id,
            uploaded_by_id=sample_user.id,
            version=3
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Create versions
        versions_data = [
            {
                "version_number": 1,
                "title": "Initial Draft",
                "content": "This is the initial content of the document.",
                "change_summary": "Initial creation",
                "prediction_status": PredictionStatus.COMPLETED,
                "prediction_score": 0.85
            },
            {
                "version_number": 2,
                "title": "First Revision",
                "content": "This is the revised content with important changes.",
                "change_summary": "Added important clauses",
                "prediction_status": PredictionStatus.COMPLETED,
                "prediction_score": 0.92
            },
            {
                "version_number": 3,
                "title": "Final Version",
                "content": "This is the final content after legal review.",
                "change_summary": "Legal review completed",
                "prediction_status": PredictionStatus.COMPLETED,
                "prediction_score": 0.98
            }
        ]
        
        for version_data in versions_data:
            version = DocumentVersion(
                document_id=document.id,
                **version_data,
                changed_by_id=sample_user.id,
                organization_id=sample_user.organization_id
            )
            db.add(version)
        
        db.commit()
        return document
    
    def test_get_version_history(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test retrieving document version history."""
        version_history = DocumentCollaborationService.get_version_history(
            db=db,
            document_id=sample_document_with_versions.id,
            organization_id=sample_user.organization_id,
            limit=50
        )
        
        assert version_history.document_id == sample_document_with_versions.id
        assert version_history.current_version == 3
        assert version_history.total_versions == 3
        assert len(version_history.versions) == 3
        
        # Check version ordering (newest first)
        assert version_history.versions[0].version_number == 3
        assert version_history.versions[1].version_number == 2
        assert version_history.versions[2].version_number == 1
        
        # Check version details
        final_version = version_history.versions[0]
        assert final_version.title == "Final Version"
        assert final_version.prediction_score == 0.98
        assert final_version.changed_by_id == sample_user.id
    
    def test_compare_versions(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test version comparison with field-level diffing."""
        comparison_request = VersionComparisonRequest(
            from_version=1,
            to_version=3,
            include_content_diff=True,
            include_metadata_diff=True,
            diff_format="unified"
        )
        
        version_diff = DocumentCollaborationService.compare_versions(
            db=db,
            document_id=sample_document_with_versions.id,
            comparison_request=comparison_request,
            organization_id=sample_user.organization_id,
            user_id=sample_user.id
        )
        
        assert version_diff.document_id == sample_document_with_versions.id
        assert version_diff.from_version == 1
        assert version_diff.to_version == 3
        assert version_diff.total_changes > 0
        assert len(version_diff.field_diffs) > 0
        assert version_diff.content_diff is not None
        assert version_diff.diff_summary is not None
        
        # Check field diffs
        title_diff = next((d for d in version_diff.field_diffs if d.field_path == "title"), None)
        assert title_diff is not None
        assert title_diff.old_value == "Initial Draft"
        assert title_diff.new_value == "Final Version"
        assert title_diff.change_type == "modified"
    
    def test_create_secure_share(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test creating a secure document share."""
        share_data = SecureShareCreate(
            recipient_email="recipient@example.com",
            recipient_name="Test Recipient",
            permission_level=SecureSharePermission.VIEW_ONLY,
            expires_at=datetime.utcnow() + timedelta(days=7),
            allowed_views=10,
            allowed_downloads=0,
            requires_authentication=False,
            track_access=True,
            share_reason="Testing secure sharing"
        )
        
        secure_share = DocumentCollaborationService.create_secure_share(
            db=db,
            document_id=sample_document_with_versions.id,
            share_data=share_data,
            organization_id=sample_user.organization_id,
            user_id=sample_user.id,
            base_url="https://test.goldleaves.com"
        )
        
        assert secure_share.document_id == sample_document_with_versions.id
        assert secure_share.recipient_email == "recipient@example.com"
        assert secure_share.permission_level == SecureSharePermission.VIEW_ONLY
        assert secure_share.allowed_views == 10
        assert secure_share.view_count == 0
        assert secure_share.is_active is True
        assert secure_share.share_slug is not None
        assert len(secure_share.share_slug) == 32
        assert "https://test.goldleaves.com/share/" in secure_share.share_url
    
    def test_access_secure_share_success(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test successful access to a secure share."""
        # Create secure share
        share_data = SecureShareCreate(
            recipient_email="viewer@example.com",
            permission_level=SecureSharePermission.VIEW_ONLY,
            allowed_views=5
        )
        
        secure_share = DocumentCollaborationService.create_secure_share(
            db=db,
            document_id=sample_document_with_versions.id,
            share_data=share_data,
            organization_id=sample_user.organization_id,
            user_id=sample_user.id
        )
        
        # Access the share
        access_request = ShareAccessRequest()
        share_access = DocumentCollaborationService.access_secure_share(
            db=db,
            share_slug=secure_share.share_slug,
            access_request=access_request,
            ip_address="192.168.1.100",
            user_agent="Test User Agent"
        )
        
        assert share_access.success is True
        assert share_access.document_title == "Collaboration Test Document"
        assert share_access.permission_level == SecureSharePermission.VIEW_ONLY
        assert share_access.remaining_views == 4  # One view used
    
    def test_access_secure_share_with_access_code(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test accessing a secure share that requires an access code."""
        # Create secure share with access code
        share_data = SecureShareCreate(
            recipient_email="secure@example.com",
            permission_level=SecureSharePermission.VIEW_ONLY,
            requires_access_code=True
        )
        
        secure_share = DocumentCollaborationService.create_secure_share(
            db=db,
            document_id=sample_document_with_versions.id,
            share_data=share_data,
            organization_id=sample_user.organization_id,
            user_id=sample_user.id
        )
        
        assert secure_share.access_code is not None
        
        # Try accessing without access code (should fail)
        access_request = ShareAccessRequest()
        with pytest.raises(ValidationError, match="Invalid access code"):
            DocumentCollaborationService.access_secure_share(
                db=db,
                share_slug=secure_share.share_slug,
                access_request=access_request
            )
        
        # Access with correct code (should succeed)
        access_request = ShareAccessRequest(access_code=secure_share.access_code)
        share_access = DocumentCollaborationService.access_secure_share(
            db=db,
            share_slug=secure_share.share_slug,
            access_request=access_request
        )
        
        assert share_access.success is True
    
    def test_access_expired_share(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test accessing an expired secure share."""
        # Create expired share
        share_data = SecureShareCreate(
            recipient_email="expired@example.com",
            permission_level=SecureSharePermission.VIEW_ONLY,
            expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        )
        
        secure_share = DocumentCollaborationService.create_secure_share(
            db=db,
            document_id=sample_document_with_versions.id,
            share_data=share_data,
            organization_id=sample_user.organization_id,
            user_id=sample_user.id
        )
        
        # Try to access expired share
        access_request = ShareAccessRequest()
        with pytest.raises(ValidationError, match="Share has expired"):
            DocumentCollaborationService.access_secure_share(
                db=db,
                share_slug=secure_share.share_slug,
                access_request=access_request
            )
    
    def test_get_document_audit_trail(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test retrieving document audit trail."""
        # Create some audit events
        audit_events = [
            DocumentAuditEvent(
                document_id=sample_document_with_versions.id,
                event_type=AuditEventType.CREATED,
                event_description="Document created",
                user_id=sample_user.id,
                organization_id=sample_user.organization_id
            ),
            DocumentAuditEvent(
                document_id=sample_document_with_versions.id,
                event_type=AuditEventType.VIEWED,
                event_description="Document viewed",
                user_id=sample_user.id,
                organization_id=sample_user.organization_id
            ),
            DocumentAuditEvent(
                document_id=sample_document_with_versions.id,
                event_type=AuditEventType.MODIFIED,
                event_description="Document modified",
                user_id=sample_user.id,
                organization_id=sample_user.organization_id
            )
        ]
        
        for event in audit_events:
            db.add(event)
        db.commit()
        
        # Get audit trail
        audit_trail = DocumentCollaborationService.get_document_audit_trail(
            db=db,
            document_id=sample_document_with_versions.id,
            organization_id=sample_user.organization_id,
            limit=100
        )
        
        assert audit_trail.document_id == sample_document_with_versions.id
        assert audit_trail.total_events >= 3
        assert len(audit_trail.events) >= 3
        assert audit_trail.event_types_summary["created"] >= 1
        assert audit_trail.event_types_summary["viewed"] >= 1
        assert audit_trail.event_types_summary["modified"] >= 1
        
        # Check event ordering (newest first)
        assert all(
            audit_trail.events[i].created_at >= audit_trail.events[i+1].created_at
            for i in range(len(audit_trail.events) - 1)
        )
    
    def test_revoke_secure_share(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test revoking a secure share."""
        # Create secure share
        share_data = SecureShareCreate(
            recipient_email="revoke@example.com",
            permission_level=SecureSharePermission.VIEW_ONLY
        )
        
        secure_share = DocumentCollaborationService.create_secure_share(
            db=db,
            document_id=sample_document_with_versions.id,
            share_data=share_data,
            organization_id=sample_user.organization_id,
            user_id=sample_user.id
        )
        
        assert secure_share.is_active is True
        
        # Revoke the share
        success = DocumentCollaborationService.revoke_secure_share(
            db=db,
            share_id=secure_share.id,
            organization_id=sample_user.organization_id,
            user_id=sample_user.id,
            revocation_reason="Testing revocation"
        )
        
        assert success is True
        
        # Check that share is now inactive
        db.refresh(secure_share)
        assert secure_share.is_active is False
        assert secure_share.revoked_at is not None
        assert secure_share.revoked_by_id == sample_user.id
        assert secure_share.revocation_reason == "Testing revocation"
    
    def test_get_collaboration_stats(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test getting organization collaboration statistics."""
        # Create some additional data for stats
        share_data = SecureShareCreate(
            recipient_email="stats@example.com",
            permission_level=SecureSharePermission.VIEW_ONLY
        )
        
        DocumentCollaborationService.create_secure_share(
            db=db,
            document_id=sample_document_with_versions.id,
            share_data=share_data,
            organization_id=sample_user.organization_id,
            user_id=sample_user.id
        )
        
        # Get collaboration stats
        collaboration_stats = DocumentCollaborationService.get_collaboration_stats(
            db=db,
            organization_id=sample_user.organization_id
        )
        
        assert collaboration_stats.total_documents >= 1
        assert collaboration_stats.total_versions >= 3
        assert collaboration_stats.total_secure_shares >= 1
        assert collaboration_stats.active_shares >= 1
        assert collaboration_stats.expired_shares >= 0
        assert len(collaboration_stats.most_collaborated_documents) >= 0


class TestDocumentCollaborationRouters:
    """Test the document collaboration API endpoints."""
    
    @pytest.fixture
    def auth_headers(self, sample_user: User) -> Dict[str, str]:
        """Create authentication headers for API requests."""
        # In a real test, you'd generate a valid JWT token
        return {"Authorization": "Bearer test_token"}
    
    def test_get_version_history_endpoint(self, auth_headers: Dict[str, str]):
        """Test the version history API endpoint."""
        with patch('services.document_collaboration.DocumentCollaborationService.get_version_history') as mock_service:
            mock_service.return_value = Mock(
                document_id=1,
                current_version=3,
                total_versions=3,
                versions=[],
                total_changes=10
            )
            
            response = client.get(
                "/documents/1/versions",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 1
            assert data["current_version"] == 3
    
    def test_compare_versions_endpoint(self, auth_headers: Dict[str, str]):
        """Test the version comparison API endpoint."""
        comparison_data = {
            "from_version": 1,
            "to_version": 3,
            "include_content_diff": True,
            "diff_format": "unified"
        }
        
        with patch('services.document_collaboration.DocumentCollaborationService.compare_versions') as mock_service:
            mock_service.return_value = Mock(
                document_id=1,
                from_version=1,
                to_version=3,
                field_diffs=[],
                total_changes=5
            )
            
            response = client.post(
                "/documents/1/compare",
                json=comparison_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 1
            assert data["from_version"] == 1
            assert data["to_version"] == 3
    
    def test_create_secure_share_endpoint(self, auth_headers: Dict[str, str]):
        """Test the secure share creation API endpoint."""
        share_data = {
            "recipient_email": "test@example.com",
            "recipient_name": "Test User",
            "permission_level": "view_only",
            "allowed_views": 10,
            "share_reason": "Testing API"
        }
        
        with patch('services.document_collaboration.DocumentCollaborationService.create_secure_share') as mock_service:
            mock_service.return_value = Mock(
                id=1,
                document_id=1,
                share_slug="test_slug_123",
                share_url="https://test.com/share/test_slug_123",
                permission_level="view_only",
                is_active=True
            )
            
            response = client.post(
                "/documents/1/share",
                json=share_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 1
            assert data["share_slug"] == "test_slug_123"
    
    def test_access_secure_share_endpoint(self):
        """Test the secure share access API endpoint."""
        with patch('services.document_collaboration.DocumentCollaborationService.access_secure_share') as mock_service:
            mock_service.return_value = Mock(
                success=True,
                document_title="Test Document",
                permission_level="view_only",
                remaining_views=9
            )
            
            response = client.get("/documents/share/test_slug_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["document_title"] == "Test Document"
    
    def test_get_audit_trail_endpoint(self, auth_headers: Dict[str, str]):
        """Test the audit trail API endpoint."""
        with patch('services.document_collaboration.DocumentCollaborationService.get_document_audit_trail') as mock_service:
            mock_service.return_value = Mock(
                document_id=1,
                total_events=10,
                events=[],
                event_types_summary={"viewed": 5, "modified": 3}
            )
            
            response = client.get(
                "/documents/1/audit",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 1
            assert data["total_events"] == 10
    
    def test_collaboration_stats_endpoint(self, auth_headers: Dict[str, str]):
        """Test the collaboration statistics API endpoint."""
        with patch('services.document_collaboration.DocumentCollaborationService.get_collaboration_stats') as mock_service:
            mock_service.return_value = Mock(
                total_documents=50,
                total_versions=200,
                total_secure_shares=25,
                active_shares=15,
                recent_collaborations=8
            )
            
            response = client.get(
                "/documents/collaboration/stats",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_documents"] == 50
            assert data["total_versions"] == 200


class TestVersionDiffing:
    """Test version diffing functionality."""
    
    def test_field_diff_generation(self):
        """Test generation of field-level diffs."""
        # Create mock versions with different content
        old_version = Mock()
        old_version.title = "Old Title"
        old_version.content = "Old content here"
        old_version.metadata = {"status": "draft", "priority": "low"}
        
        new_version = Mock()
        new_version.title = "New Title"
        new_version.content = "New content with changes"
        new_version.metadata = {"status": "final", "priority": "high", "reviewed": True}
        
        # Test diff generation
        field_diffs = DocumentCollaborationService._generate_field_diffs(old_version, new_version)
        
        assert len(field_diffs) >= 3  # title, content, metadata changes
        
        # Check title diff
        title_diff = next((d for d in field_diffs if d.field_path == "title"), None)
        assert title_diff is not None
        assert title_diff.old_value == "Old Title"
        assert title_diff.new_value == "New Title"
        assert title_diff.change_type == "modified"
    
    def test_content_diff_generation(self):
        """Test content diffing with unified format."""
        old_content = "This is line 1\nThis is line 2\nThis is line 3"
        new_content = "This is line 1\nThis is modified line 2\nThis is line 3\nThis is new line 4"
        
        content_diff = DocumentCollaborationService._generate_content_diff(
            old_content, new_content, "unified"
        )
        
        assert content_diff.diff_format == "unified"
        assert content_diff.additions_count > 0
        assert content_diff.deletions_count > 0
        assert "modified line 2" in content_diff.diff_content or "new line 4" in content_diff.diff_content


class TestSecureSharing:
    """Test secure sharing functionality."""
    
    def test_share_slug_generation(self):
        """Test that share slugs are properly generated."""
        from models.document import DocumentSecureShare
        
        slug1 = DocumentSecureShare._generate_slug()
        slug2 = DocumentSecureShare._generate_slug()
        
        assert len(slug1) == 32
        assert len(slug2) == 32
        assert slug1 != slug2
        assert slug1.isalnum()
        assert slug2.isalnum()
    
    def test_access_code_generation(self):
        """Test access code generation."""
        from models.document import DocumentSecureShare
        
        code1 = DocumentSecureShare._generate_access_code()
        code2 = DocumentSecureShare._generate_access_code()
        
        assert len(code1) == 8
        assert len(code2) == 8
        assert code1 != code2
        assert code1.isalnum()
        assert code2.isalnum()
    
    def test_share_validation(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test share validation logic."""
        # Create a share with specific limits
        secure_share = DocumentSecureShare(
            document_id=sample_document_with_versions.id,
            permission_level=SecureSharePermission.VIEW_ONLY,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            allowed_views=3,
            view_count=0,
            is_active=True,
            organization_id=sample_user.organization_id
        )
        
        # Test validity
        assert secure_share.is_valid() is True
        assert secure_share.is_expired() is False
        
        # Test after expiration
        secure_share.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert secure_share.is_expired() is True
        assert secure_share.is_valid() is False
        
        # Test after view limit reached
        secure_share.expires_at = datetime.utcnow() + timedelta(hours=1)
        secure_share.view_count = 3
        assert secure_share.is_valid() is False
        
        # Test after deactivation
        secure_share.view_count = 0
        secure_share.is_active = False
        assert secure_share.is_valid() is False


class TestAuditTrail:
    """Test audit trail functionality."""
    
    def test_audit_event_creation(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test creating audit events."""
        event = DocumentAuditEvent(
            document_id=sample_document_with_versions.id,
            event_type=AuditEventType.VIEWED,
            event_description="Document accessed via secure share",
            user_id=sample_user.id,
            ip_address="192.168.1.100",
            metadata={"share_id": 123, "access_method": "secure_link"},
            organization_id=sample_user.organization_id
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        assert event.id is not None
        assert event.event_type == AuditEventType.VIEWED
        assert event.metadata["share_id"] == 123
        assert event.created_at is not None
    
    def test_audit_event_filtering(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test filtering audit events by type."""
        # Create multiple event types
        events = [
            DocumentAuditEvent(
                document_id=sample_document_with_versions.id,
                event_type=AuditEventType.VIEWED,
                event_description="Document viewed",
                user_id=sample_user.id,
                organization_id=sample_user.organization_id
            ),
            DocumentAuditEvent(
                document_id=sample_document_with_versions.id,
                event_type=AuditEventType.DOWNLOADED,
                event_description="Document downloaded",
                user_id=sample_user.id,
                organization_id=sample_user.organization_id
            ),
            DocumentAuditEvent(
                document_id=sample_document_with_versions.id,
                event_type=AuditEventType.SHARED,
                event_description="Document shared",
                user_id=sample_user.id,
                organization_id=sample_user.organization_id
            )
        ]
        
        for event in events:
            db.add(event)
        db.commit()
        
        # Test filtering by event types
        audit_trail = DocumentCollaborationService.get_document_audit_trail(
            db=db,
            document_id=sample_document_with_versions.id,
            organization_id=sample_user.organization_id,
            event_types=[AuditEventType.VIEWED, AuditEventType.DOWNLOADED]
        )
        
        # Should only return viewed and downloaded events
        returned_types = {event.event_type for event in audit_trail.events}
        assert AuditEventType.VIEWED in returned_types
        assert AuditEventType.DOWNLOADED in returned_types
        assert AuditEventType.SHARED not in returned_types


# Integration tests

class TestCollaborationIntegration:
    """Test integration between collaboration features."""
    
    def test_version_creation_triggers_audit_event(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test that creating version comparisons creates audit events."""
        initial_audit_count = db.query(DocumentAuditEvent).filter(
            DocumentAuditEvent.document_id == sample_document_with_versions.id
        ).count()
        
        # Compare versions (should create audit event)
        comparison_request = VersionComparisonRequest(
            from_version=1,
            to_version=2,
            include_content_diff=True
        )
        
        DocumentCollaborationService.compare_versions(
            db=db,
            document_id=sample_document_with_versions.id,
            comparison_request=comparison_request,
            organization_id=sample_user.organization_id,
            user_id=sample_user.id
        )
        
        # Check that audit event was created
        final_audit_count = db.query(DocumentAuditEvent).filter(
            DocumentAuditEvent.document_id == sample_document_with_versions.id
        ).count()
        
        assert final_audit_count > initial_audit_count
    
    def test_share_access_creates_audit_trail(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test that accessing shares creates proper audit trail."""
        # Create secure share
        share_data = SecureShareCreate(
            recipient_email="audit@example.com",
            permission_level=SecureSharePermission.VIEW_ONLY,
            track_access=True
        )
        
        secure_share = DocumentCollaborationService.create_secure_share(
            db=db,
            document_id=sample_document_with_versions.id,
            share_data=share_data,
            organization_id=sample_user.organization_id,
            user_id=sample_user.id
        )
        
        # Access the share
        access_request = ShareAccessRequest()
        DocumentCollaborationService.access_secure_share(
            db=db,
            share_slug=secure_share.share_slug,
            access_request=access_request,
            ip_address="192.168.1.200",
            user_agent="Test Agent"
        )
        
        # Check that access log was created
        access_logs = db.query(DocumentShareAccessLog).filter(
            DocumentShareAccessLog.secure_share_id == secure_share.id
        ).all()
        
        assert len(access_logs) > 0
        assert access_logs[0].access_type == "view"
        assert access_logs[0].ip_address == "192.168.1.200"
        assert access_logs[0].success is True
    
    def test_collaboration_workflow(self, db: Session, sample_document_with_versions: Document, sample_user: User):
        """Test a complete collaboration workflow."""
        # 1. Get version history
        version_history = DocumentCollaborationService.get_version_history(
            db=db,
            document_id=sample_document_with_versions.id,
            organization_id=sample_user.organization_id
        )
        assert len(version_history.versions) > 0
        
        # 2. Compare versions
        comparison_request = VersionComparisonRequest(
            from_version=1,
            to_version=version_history.current_version,
            include_content_diff=True
        )
        
        version_diff = DocumentCollaborationService.compare_versions(
            db=db,
            document_id=sample_document_with_versions.id,
            comparison_request=comparison_request,
            organization_id=sample_user.organization_id,
            user_id=sample_user.id
        )
        assert version_diff.total_changes > 0
        
        # 3. Create secure share
        share_data = SecureShareCreate(
            recipient_email="workflow@example.com",
            permission_level=SecureSharePermission.VIEW_ONLY,
            allowed_views=5
        )
        
        secure_share = DocumentCollaborationService.create_secure_share(
            db=db,
            document_id=sample_document_with_versions.id,
            share_data=share_data,
            organization_id=sample_user.organization_id,
            user_id=sample_user.id
        )
        assert secure_share.is_active is True
        
        # 4. Access the share
        access_request = ShareAccessRequest()
        share_access = DocumentCollaborationService.access_secure_share(
            db=db,
            share_slug=secure_share.share_slug,
            access_request=access_request
        )
        assert share_access.success is True
        
        # 5. Get audit trail
        audit_trail = DocumentCollaborationService.get_document_audit_trail(
            db=db,
            document_id=sample_document_with_versions.id,
            organization_id=sample_user.organization_id
        )
        assert audit_trail.total_events > 0
        
        # 6. Get collaboration stats
        collaboration_stats = DocumentCollaborationService.get_collaboration_stats(
            db=db,
            organization_id=sample_user.organization_id
        )
        assert collaboration_stats.total_documents > 0
        assert collaboration_stats.total_secure_shares > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
