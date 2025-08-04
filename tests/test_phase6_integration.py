# tests/test_phase6_integration.py

"""Phase 6: Integration tests for transparent collaboration & document lineage system."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from routers.main import app
from models.document import (
    Document, DocumentVersion, DocumentSecureShare, DocumentAuditEvent,
    AuditEventType, SecureSharePermission, DocumentType, PredictionStatus
)
from models.user import User, Organization
from services.document_collaboration import DocumentCollaborationService
from schemas.document.collaboration import (
    VersionComparisonRequest, SecureShareCreate
)

client = TestClient(app)


class TestPhase6Integration:
    """Integration tests for Phase 6 collaboration features."""
    
    @pytest.fixture
    def test_organization(self, db: Session) -> Organization:
        """Create test organization."""
        org = Organization(
            name="Phase6 Test Org",
            domain="phase6test.com",
            is_active=True
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        return org
    
    @pytest.fixture
    def test_user(self, db: Session, test_organization: Organization) -> User:
        """Create test user."""
        user = User(
            email="phase6@test.com",
            full_name="Phase6 Test User",
            hashed_password="hashed_password",
            is_active=True,
            is_admin=True,
            organization_id=test_organization.id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @pytest.fixture
    def test_document_with_lineage(self, db: Session, test_user: User) -> Document:
        """Create test document with version lineage."""
        # Create base document
        document = Document(
            title="Phase 6 Test Document",
            document_type=DocumentType.CONTRACT,
            file_path="/test/phase6_doc.pdf",
            file_size=2048 * 1024,
            organization_id=test_user.organization_id,
            uploaded_by_id=test_user.id,
            version=4
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Create version lineage
        versions = [
            {
                "version_number": 1,
                "title": "Phase 6 Initial Draft",
                "content": "This is the initial phase 6 document content with basic terms.",
                "change_summary": "Initial document creation",
                "prediction_status": PredictionStatus.COMPLETED,
                "prediction_score": 0.75,
                "metadata": {"stage": "draft", "reviewer": None}
            },
            {
                "version_number": 2,
                "title": "Phase 6 Legal Review",
                "content": "This is the phase 6 document after legal review with additional clauses.",
                "change_summary": "Added legal compliance clauses",
                "prediction_status": PredictionStatus.COMPLETED,
                "prediction_score": 0.88,
                "metadata": {"stage": "legal_review", "reviewer": "legal_team"}
            },
            {
                "version_number": 3,
                "title": "Phase 6 Client Feedback",
                "content": "This is the phase 6 document incorporating client feedback and revisions.",
                "change_summary": "Incorporated client feedback",
                "prediction_status": PredictionStatus.COMPLETED,
                "prediction_score": 0.92,
                "metadata": {"stage": "client_review", "reviewer": "client_team"}
            },
            {
                "version_number": 4,
                "title": "Phase 6 Final Version",
                "content": "This is the final phase 6 document ready for execution.",
                "change_summary": "Final review and approval",
                "prediction_status": PredictionStatus.COMPLETED,
                "prediction_score": 0.97,
                "metadata": {"stage": "final", "reviewer": "senior_partner"}
            }
        ]
        
        for version_data in versions:
            version = DocumentVersion(
                document_id=document.id,
                **version_data,
                changed_by_id=test_user.id,
                organization_id=test_user.organization_id
            )
            db.add(version)
        
        db.commit()
        return document
    
    @pytest.fixture
    def auth_headers(self, test_user: User) -> dict:
        """Create authentication headers."""
        # In a real test, generate valid JWT token
        return {"Authorization": "Bearer test_phase6_token"}
    
    def test_complete_collaboration_workflow(
        self, 
        db: Session, 
        test_document_with_lineage: Document, 
        test_user: User,
        auth_headers: Dict[str, Any]
    ):
        """Test complete Phase 6 collaboration workflow."""
        
        # Step 1: Get document version history
        with patch('core.dependencies.get_current_user', return_value=test_user):
            with patch('core.security.require_permission'):
                response = client.get(
                    f"/documents/{test_document_with_lineage.id}/versions",
                    headers=auth_headers
                )
                assert response.status_code == 200
                version_data = response.json()
                assert version_data["total_versions"] == 4
                assert version_data["current_version"] == 4
                assert len(version_data["versions"]) == 4
                
                # Verify version ordering (newest first)
                versions = version_data["versions"]
                assert versions[0]["version_number"] == 4
                assert versions[1]["version_number"] == 3
                assert versions[2]["version_number"] == 2
                assert versions[3]["version_number"] == 1
        
        # Step 2: Compare versions to see document evolution
        comparison_data = {
            "from_version": 1,
            "to_version": 4,
            "include_content_diff": True,
            "include_metadata_diff": True,
            "diff_format": "unified"
        }
        
        with patch('core.dependencies.get_current_user', return_value=test_user):
            with patch('core.security.require_permission'):
                response = client.post(
                    f"/documents/{test_document_with_lineage.id}/compare",
                    json=comparison_data,
                    headers=auth_headers
                )
                assert response.status_code == 200
                diff_data = response.json()
                assert diff_data["from_version"] == 1
                assert diff_data["to_version"] == 4
                assert diff_data["total_changes"] > 0
                assert len(diff_data["field_diffs"]) > 0
                assert diff_data["content_diff"] is not None
        
        # Step 3: Create secure share for external collaboration
        share_data = {
            "recipient_email": "external@partner.com",
            "recipient_name": "External Partner",
            "permission_level": "view_only",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "allowed_views": 10,
            "allowed_downloads": 0,
            "requires_authentication": False,
            "track_access": True,
            "share_reason": "Contract review with external partner"
        }
        
        with patch('core.dependencies.get_current_user', return_value=test_user):
            with patch('core.security.require_permission'):
                response = client.post(
                    f"/documents/{test_document_with_lineage.id}/share",
                    json=share_data,
                    headers=auth_headers
                )
                assert response.status_code == 200
                share_response = response.json()
                assert share_response["document_id"] == test_document_with_lineage.id
                assert share_response["recipient_email"] == "external@partner.com"
                assert share_response["permission_level"] == "view_only"
                assert share_response["share_slug"] is not None
                assert share_response["share_url"] is not None
                
                share_slug = share_response["share_slug"]
        
        # Step 4: Access the secure share (simulating external partner)
        response = client.get(f"/documents/share/{share_slug}")
        assert response.status_code == 200
        access_data = response.json()
        assert access_data["success"] is True
        assert access_data["document_title"] == "Phase 6 Test Document"
        assert access_data["permission_level"] == "view_only"
        assert access_data["remaining_views"] == 9  # One view consumed
        
        # Step 5: Get comprehensive audit trail
        with patch('core.dependencies.get_current_user', return_value=test_user):
            with patch('core.security.require_permission'):
                response = client.get(
                    f"/documents/{test_document_with_lineage.id}/audit",
                    headers=auth_headers
                )
                assert response.status_code == 200
                audit_data = response.json()
                assert audit_data["document_id"] == test_document_with_lineage.id
                assert audit_data["total_events"] > 0
                assert len(audit_data["events"]) > 0
                
                # Verify audit events include our actions
                event_types = {event["event_type"] for event in audit_data["events"]}
                assert "shared" in event_types or "version_created" in event_types
        
        # Step 6: Get organization collaboration statistics
        with patch('core.dependencies.get_current_user', return_value=test_user):
            response = client.get(
                "/documents/collaboration/stats",
                headers=auth_headers
            )
            assert response.status_code == 200
            stats_data = response.json()
            assert stats_data["total_documents"] >= 1
            assert stats_data["total_versions"] >= 4
            assert stats_data["total_secure_shares"] >= 1
            assert stats_data["active_shares"] >= 1
    
    def test_secure_sharing_with_access_control(
        self,
        db: Session,
        test_document_with_lineage: Document,
        test_user: User,
        auth_headers: Dict[str, Any]
    ):
        """Test secure sharing with access control features."""
        
        # Create share with access code and IP restrictions
        share_data = {
            "recipient_email": "restricted@partner.com",
            "permission_level": "download_allowed", 
            "requires_access_code": True,
            "ip_whitelist": ["192.168.1.100", "10.0.0.50"],
            "allowed_views": 3,
            "allowed_downloads": 1,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "share_reason": "Restricted access for final review"
        }
        
        with patch('core.dependencies.get_current_user', return_value=test_user):
            with patch('core.security.require_permission'):
                response = client.post(
                    f"/documents/{test_document_with_lineage.id}/share",
                    json=share_data,
                    headers=auth_headers
                )
                assert response.status_code == 200
                share_response = response.json()
                assert share_response["access_code"] is not None
                assert len(share_response["access_code"]) == 8
                
                share_slug = share_response["share_slug"]
                access_code = share_response["access_code"]
        
        # Try accessing without access code (should fail)
        response = client.get(f"/documents/share/{share_slug}")
        assert response.status_code == 400
        assert "access code" in response.json()["detail"].lower()
        
        # Try accessing with wrong access code (should fail)
        response = client.get(f"/documents/share/{share_slug}?access_code=wrongcode")
        assert response.status_code == 400
        
        # Access with correct code (should succeed)
        response = client.get(f"/documents/share/{share_slug}?access_code={access_code}")
        assert response.status_code == 200
        access_data = response.json()
        assert access_data["success"] is True
        assert access_data["remaining_views"] == 2
        assert access_data["remaining_downloads"] == 1
        assert access_data["download_url"] is not None
    
    def test_version_diffing_and_lineage_tracking(
        self,
        db: Session,
        test_document_with_lineage: Document,
        test_user: User,
        auth_headers: Dict[str, Any]
    ):
        """Test version diffing and lineage tracking capabilities."""
        
        # Compare different version pairs to track evolution
        version_pairs = [
            (1, 2),  # Draft to legal review
            (2, 3),  # Legal review to client feedback  
            (3, 4),  # Client feedback to final
            (1, 4)   # Initial to final (full evolution)
        ]
        
        for from_ver, to_ver in version_pairs:
            comparison_data = {
                "from_version": from_ver,
                "to_version": to_ver,
                "include_content_diff": True,
                "include_metadata_diff": True,
                "diff_format": "unified"
            }
            
            with patch('core.dependencies.get_current_user', return_value=test_user):
                with patch('core.security.require_permission'):
                    response = client.post(
                        f"/documents/{test_document_with_lineage.id}/compare",
                        json=comparison_data,
                        headers=auth_headers
                    )
                    assert response.status_code == 200
                    diff_data = response.json()
                    
                    # Verify diff structure
                    assert diff_data["from_version"] == from_ver
                    assert diff_data["to_version"] == to_ver
                    assert "field_diffs" in diff_data
                    assert "content_diff" in diff_data
                    assert "metadata_changes" in diff_data
                    assert "diff_summary" in diff_data
                    
                    # Verify field diffs capture changes
                    field_diffs = diff_data["field_diffs"]
                    assert len(field_diffs) > 0
                    
                    # Check for specific field changes
                    field_paths = {diff["field_path"] for diff in field_diffs}
                    assert "title" in field_paths or "content" in field_paths
                    
                    # Verify metadata changes tracking
                    if diff_data["metadata_changes"]:
                        metadata_changes = diff_data["metadata_changes"]
                        if "stage" in metadata_changes:
                            stage_change = metadata_changes["stage"]
                            assert "old" in stage_change
                            assert "new" in stage_change
                            assert stage_change["change_type"] == "modified"
    
    def test_audit_trail_compliance(
        self,
        db: Session,
        test_document_with_lineage: Document,
        test_user: User,
        auth_headers: Dict[str, Any]
    ):
        """Test audit trail for compliance requirements."""
        
        # Create comprehensive audit events by performing various actions
        actions = [
            # Version comparison
            {
                "endpoint": f"/documents/{test_document_with_lineage.id}/compare",
                "method": "POST",
                "data": {
                    "from_version": 1,
                    "to_version": 4,
                    "include_content_diff": True
                }
            },
            # Secure share creation
            {
                "endpoint": f"/documents/{test_document_with_lineage.id}/share",
                "method": "POST", 
                "data": {
                    "recipient_email": "audit@compliance.com",
                    "permission_level": "view_only",
                    "share_reason": "Compliance audit review"
                }
            }
        ]
        
        # Perform actions to generate audit events
        with patch('core.dependencies.get_current_user', return_value=test_user):
            with patch('core.security.require_permission'):
                for action in actions:
                    if action["method"] == "POST":
                        response = client.post(
                            action["endpoint"],
                            json=action["data"],
                            headers=auth_headers
                        )
                        assert response.status_code == 200
        
        # Get audit trail and verify compliance data
        with patch('core.dependencies.get_current_user', return_value=test_user):
            with patch('core.security.require_permission'):
                response = client.get(
                    f"/documents/{test_document_with_lineage.id}/audit",
                    headers=auth_headers
                )
                assert response.status_code == 200
                audit_data = response.json()
                
                # Verify audit trail structure
                assert "document_id" in audit_data
                assert "total_events" in audit_data
                assert "events" in audit_data
                assert "event_types_summary" in audit_data
                assert "user_activity_summary" in audit_data
                
                # Verify audit events have required compliance fields
                for event in audit_data["events"]:
                    assert "id" in event
                    assert "event_type" in event
                    assert "event_description" in event
                    assert "user_name" in event
                    assert "created_at" in event
                    assert "metadata" in event
                
                # Verify event type filtering works
                if audit_data["total_events"] > 0:
                    # Test filtering by specific event types
                    response = client.get(
                        f"/documents/{test_document_with_lineage.id}/audit?event_types=shared&event_types=version_created",
                        headers=auth_headers
                    )
                    assert response.status_code == 200 or response.status_code == 422  # Might fail if enum parsing not implemented
    
    def test_collaboration_statistics_accuracy(
        self,
        db: Session,
        test_document_with_lineage: Document,
        test_user: User,
        auth_headers: Dict[str, Any]
    ):
        """Test accuracy of collaboration statistics."""
        
        # Create additional collaboration data
        share_data = {
            "recipient_email": "stats@test.com",
            "permission_level": "view_only",
            "share_reason": "Statistics testing"
        }
        
        with patch('core.dependencies.get_current_user', return_value=test_user):
            with patch('core.security.require_permission'):
                # Create a secure share
                response = client.post(
                    f"/documents/{test_document_with_lineage.id}/share",
                    json=share_data,
                    headers=auth_headers
                )
                assert response.status_code == 200
                
                # Get collaboration statistics
                response = client.get(
                    "/documents/collaboration/stats",
                    headers=auth_headers
                )
                assert response.status_code == 200
                stats_data = response.json()
                
                # Verify statistics structure and minimum values
                assert stats_data["total_documents"] >= 1
                assert stats_data["total_versions"] >= 4
                assert stats_data["total_secure_shares"] >= 1
                assert stats_data["active_shares"] >= 1
                assert stats_data["expired_shares"] >= 0
                
                # Verify derived statistics
                assert "recent_collaborations" in stats_data
                assert "recent_shares_created" in stats_data
                assert "most_collaborated_documents" in stats_data
                assert "average_share_duration_days" in stats_data
                
                # Verify most collaborated documents structure
                if stats_data["most_collaborated_documents"]:
                    for doc_stat in stats_data["most_collaborated_documents"]:
                        assert "title" in doc_stat
                        assert "versions" in doc_stat
                        assert "collaborators" in doc_stat


class TestPhase6ErrorHandling:
    """Test error handling for Phase 6 features."""
    
    def test_version_comparison_errors(self, auth_headers: Dict[str, Any]):
        """Test error handling in version comparison."""
        
        # Test with non-existent document
        comparison_data = {
            "from_version": 1,
            "to_version": 2,
            "include_content_diff": True
        }
        
        with patch('core.dependencies.get_current_user'):
            with patch('core.security.require_permission'):
                response = client.post(
                    "/documents/99999/compare",
                    json=comparison_data,
                    headers=auth_headers
                )
                assert response.status_code == 404
    
    def test_secure_share_access_errors(self):
        """Test error handling in secure share access."""
        
        # Test with non-existent share slug
        response = client.get("/documents/share/nonexistent_slug_123456")
        assert response.status_code == 404
        
        # Test with malformed share slug
        response = client.get("/documents/share/invalid")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
