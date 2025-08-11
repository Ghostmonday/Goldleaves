"""
Tests for entitlement service and authorization decorators.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from core.entitlements import EntitlementService, requires_plan, requires_feature
from models.entitlement import Entitlement, PlanType
from models.user import User


class TestEntitlementService:
    """Test entitlement service functionality."""
    
    def test_get_current_entitlement_user_level(self, db_session):
        """Test getting user-level entitlement."""
        # Create test user and entitlement
        user = User(id=1, email="test@example.com", hashed_password="test")
        entitlement = Entitlement(
            user_id=1,
            plan=PlanType.PRO,
            features={"test": True},
            active=True
        )
        
        db_session.add(user)
        db_session.add(entitlement)
        db_session.commit()
        
        # Test getting entitlement
        result = EntitlementService.get_current_entitlement(user, db=db_session)
        
        assert result is not None
        assert result.user_id == 1
        assert result.plan == PlanType.PRO
        assert result.active is True
    
    def test_get_current_entitlement_tenant_level(self, db_session):
        """Test getting tenant-level entitlement (organization)."""
        # Create test user and organization entitlement
        user = User(id=1, email="test@example.com", hashed_password="test")
        entitlement = Entitlement(
            tenant_id=123,
            plan=PlanType.TEAM,
            features={"team_features": True},
            active=True
        )
        
        db_session.add(user)
        db_session.add(entitlement)
        db_session.commit()
        
        # Test getting entitlement with tenant_id
        result = EntitlementService.get_current_entitlement(
            user, tenant_id=123, db=db_session
        )
        
        assert result is not None
        assert result.tenant_id == 123
        assert result.plan == PlanType.TEAM
        assert result.active is True
    
    def test_get_current_entitlement_none(self, db_session):
        """Test getting entitlement when none exists."""
        user = User(id=1, email="test@example.com", hashed_password="test")
        db_session.add(user)
        db_session.commit()
        
        result = EntitlementService.get_current_entitlement(user, db=db_session)
        
        assert result is None
    
    def test_check_plan_access_with_entitlement(self, db_session):
        """Test checking plan access with active entitlement."""
        user = User(id=1, email="test@example.com", hashed_password="test")
        entitlement = Entitlement(
            user_id=1,
            plan=PlanType.PRO,
            active=True
        )
        
        db_session.add(user)
        db_session.add(entitlement)
        db_session.commit()
        
        # Test access check
        has_access = EntitlementService.check_plan_access(
            user, [PlanType.PRO, PlanType.TEAM], db=db_session
        )
        
        assert has_access is True
        
        # Test denied access
        has_access = EntitlementService.check_plan_access(
            user, [PlanType.TEAM], db=db_session
        )
        
        assert has_access is False
    
    def test_check_plan_access_no_entitlement_free_allowed(self, db_session):
        """Test plan access when no entitlement exists but FREE is allowed."""
        user = User(id=1, email="test@example.com", hashed_password="test")
        db_session.add(user)
        db_session.commit()
        
        # Should allow access if FREE is in required plans
        has_access = EntitlementService.check_plan_access(
            user, [PlanType.FREE, PlanType.PRO], db=db_session
        )
        
        assert has_access is True
        
        # Should deny access if FREE is not in required plans
        has_access = EntitlementService.check_plan_access(
            user, [PlanType.PRO, PlanType.TEAM], db=db_session
        )
        
        assert has_access is False
    
    def test_check_feature_access(self, db_session):
        """Test checking feature access."""
        user = User(id=1, email="test@example.com", hashed_password="test")
        entitlement = Entitlement(
            user_id=1,
            plan=PlanType.PRO,
            features={"advanced_analytics": True, "priority_support": True},
            active=True
        )
        
        db_session.add(user)
        db_session.add(entitlement)
        db_session.commit()
        
        # Test feature access
        has_feature = EntitlementService.check_feature_access(
            user, "advanced_analytics", db=db_session
        )
        assert has_feature is True
        
        # Test missing feature
        has_feature = EntitlementService.check_feature_access(
            user, "custom_integrations", db=db_session
        )
        assert has_feature is False
    
    def test_get_feature_limit(self, db_session):
        """Test getting feature limits."""
        user = User(id=1, email="test@example.com", hashed_password="test")
        entitlement = Entitlement(
            user_id=1,
            plan=PlanType.PRO,
            features={"api_requests_per_month": 50000, "storage_gb": 100},
            active=True
        )
        
        db_session.add(user)
        db_session.add(entitlement)
        db_session.commit()
        
        # Test getting limit
        limit = EntitlementService.get_feature_limit(
            user, "api_requests_per_month", db=db_session
        )
        assert limit == 50000
        
        # Test default limit
        limit = EntitlementService.get_feature_limit(
            user, "nonexistent_feature", default_limit=999, db=db_session
        )
        assert limit == 999


class TestAuthorizationDecorators:
    """Test authorization decorators."""
    
    @patch('core.entitlements.get_current_active_user')
    @patch('core.entitlements.get_db')
    @patch('core.entitlements.EntitlementService.check_plan_access')
    def test_requires_plan_decorator_success(
        self, mock_check_access, mock_get_db, mock_get_user
    ):
        """Test requires_plan decorator with sufficient access."""
        # Setup mocks
        mock_user = Mock(id=1)
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        mock_check_access.return_value = True
        
        # Create decorated function
        @requires_plan("PRO", "TEAM")
        def test_function():
            return "success"
        
        # Test function call
        result = test_function()
        
        assert result == "success"
        mock_check_access.assert_called_once_with(
            user=mock_user,
            required_plans=[PlanType.PRO, PlanType.TEAM],
            tenant_id=None,
            db=mock_get_db.return_value
        )
    
    @patch('core.entitlements.get_current_active_user')
    @patch('core.entitlements.get_db')
    @patch('core.entitlements.EntitlementService.check_plan_access')
    def test_requires_plan_decorator_access_denied(
        self, mock_check_access, mock_get_db, mock_get_user
    ):
        """Test requires_plan decorator with insufficient access."""
        # Setup mocks
        mock_user = Mock(id=1)
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        mock_check_access.return_value = False
        
        # Create decorated function
        @requires_plan("PRO")
        def test_function():
            return "success"
        
        # Test function call should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            test_function()
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in str(exc_info.value.detail)
        assert "PRO" in str(exc_info.value.detail)
    
    @patch('core.entitlements.get_current_active_user')
    @patch('core.entitlements.get_db')
    @patch('core.entitlements.EntitlementService.check_feature_access')
    def test_requires_feature_decorator_success(
        self, mock_check_access, mock_get_db, mock_get_user
    ):
        """Test requires_feature decorator with feature access."""
        # Setup mocks
        mock_user = Mock(id=1)
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        mock_check_access.return_value = True
        
        # Create decorated function
        @requires_feature("advanced_analytics")
        def test_function():
            return "analytics_data"
        
        # Test function call
        result = test_function()
        
        assert result == "analytics_data"
        mock_check_access.assert_called_once_with(
            user=mock_user,
            feature_name="advanced_analytics",
            tenant_id=None,
            db=mock_get_db.return_value
        )
    
    @patch('core.entitlements.get_current_active_user')
    @patch('core.entitlements.get_db')
    @patch('core.entitlements.EntitlementService.check_feature_access')
    def test_requires_feature_decorator_access_denied(
        self, mock_check_access, mock_get_db, mock_get_user
    ):
        """Test requires_feature decorator without feature access."""
        # Setup mocks
        mock_user = Mock(id=1)
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        mock_check_access.return_value = False
        
        # Create decorated function
        @requires_feature("advanced_analytics")
        def test_function():
            return "analytics_data"
        
        # Test function call should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            test_function()
        
        assert exc_info.value.status_code == 403
        assert "advanced_analytics" in str(exc_info.value.detail)


@pytest.fixture
def db_session():
    """Create a test database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models.base import Base
    
    # Create in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()