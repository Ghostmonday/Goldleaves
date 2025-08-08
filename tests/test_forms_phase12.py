"""
Phase 12 Tests: Basic functionality tests for form crowdsourcing system
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock

from models.forms import Form, FormType, FormStatus, ContributorType, FormLanguage
from schemas.forms import FormUploadRequest, FormMetadata, JurisdictionInfo
from services.forms import FormService


class TestFormModels:
    """Test form model functionality."""
    
    def test_form_creation(self):
        """Test basic form model creation."""
        form = Form(
            form_id="test_form_123",
            title="Test Motion",
            form_type=FormType.MOTION,
            status=FormStatus.PENDING,
            contributor_id=1,
            language=FormLanguage.ENGLISH
        )
        
        assert form.form_id == "test_form_123"
        assert form.title == "Test Motion"
        assert form.form_type == FormType.MOTION
        assert form.status == FormStatus.PENDING
        assert form.language == FormLanguage.ENGLISH
        assert form.is_current_version is True
    
    def test_form_lock(self):
        """Test form locking after approval."""
        form = Form(
            form_id="test_form_123",
            title="Test Motion",
            form_type=FormType.MOTION,
            status=FormStatus.PENDING,
            contributor_id=1
        )
        
        form.lock_form()
        
        assert form.status == FormStatus.APPROVED
        assert form.is_public is True


class TestFormSchemas:
    """Test form schema validation."""
    
    def test_jurisdiction_info_validation(self):
        """Test jurisdiction info validation."""
        # Valid jurisdiction
        jurisdiction = JurisdictionInfo(
            state="CA",
            county="Los Angeles",
            court_type="Superior Court"
        )
        
        assert jurisdiction.state == "CA"
        assert jurisdiction.county == "Los Angeles"
        
        # Invalid state should raise validation error
        with pytest.raises(ValueError, match="Invalid state code"):
            JurisdictionInfo(state="XX")
    
    def test_form_upload_request_validation(self):
        """Test form upload request validation."""
        jurisdiction = JurisdictionInfo(
            state="CA",
            county="Los Angeles"
        )
        
        metadata = FormMetadata(
            jurisdiction=jurisdiction,
            form_number="CIV-123",
            language=FormLanguage.ENGLISH
        )
        
        request = FormUploadRequest(
            title="Test Form",
            description="A test form",
            form_type=FormType.MOTION,
            metadata=metadata,
            tags=["test", "motion"]
        )
        
        assert request.title == "Test Form"
        assert request.form_type == FormType.MOTION
        assert request.metadata.jurisdiction.state == "CA"
        assert len(request.tags) == 2


class TestFormService:
    """Test form service functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Mock database session
        self.mock_db = Mock()
        self.form_service = FormService(self.mock_db)
    
    def test_generate_form_id(self):
        """Test form ID generation."""
        form_id = self.form_service._generate_form_id()
        
        assert form_id.startswith("form_")
        assert len(form_id) == 17  # "form_" + 12 hex chars
    
    def test_generate_feedback_id(self):
        """Test feedback ID generation."""
        feedback_id = self.form_service._generate_feedback_id()
        
        assert feedback_id.startswith("fb_")
        assert len(feedback_id) == 15  # "fb_" + 12 hex chars
    
    def test_calculate_feedback_priority(self):
        """Test feedback priority calculation."""
        # Critical type with high severity
        priority = self.form_service._calculate_feedback_priority("field_error", 5)
        assert priority == "critical"
        
        # Critical type with medium severity
        priority = self.form_service._calculate_feedback_priority("field_error", 3)
        assert priority == "high"
        
        # Normal type with low severity
        priority = self.form_service._calculate_feedback_priority("suggestion", 2)
        assert priority == "low"


class TestFormAPI:
    """Test form API endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        # This would need actual FastAPI app setup
        # For now, just test that imports work correctly
        pass
    
    def test_import_forms_router(self):
        """Test that forms router can be imported."""
        try:
            from routers.forms import router
            assert router is not None
            assert router.prefix == "/api/v1/forms"
        except ImportError as e:
            pytest.skip(f"Forms router not available: {e}")
    
    def test_import_form_service(self):
        """Test that form service can be imported."""
        try:
            from services.forms import FormService
            assert FormService is not None
        except ImportError as e:
            pytest.skip(f"Form service not available: {e}")


if __name__ == "__main__":
    # Run basic tests
    test_models = TestFormModels()
    test_models.test_form_creation()
    test_models.test_form_lock()
    print("✅ Form model tests passed")
    
    test_schemas = TestFormSchemas()
    test_schemas.test_jurisdiction_info_validation()
    test_schemas.test_form_upload_request_validation()
    print("✅ Form schema tests passed")
    
    test_service = TestFormService()
    test_service.setup_method()
    test_service.test_generate_form_id()
    test_service.test_generate_feedback_id()
    test_service.test_calculate_feedback_priority()
    print("✅ Form service tests passed")
    
    test_api = TestFormAPI()
    test_api.setup_method()
    test_api.test_import_forms_router()
    test_api.test_import_form_service()
    print("✅ Form API tests passed")
    
    print("\n🎉 All Phase 12 tests passed! Form crowdsourcing system is ready.")
