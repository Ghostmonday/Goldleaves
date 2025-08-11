"""
Tests for billing router endpoints.
"""

import json
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routers.billing import router
from models.user import User
from models.entitlement import Entitlement, PlanType


class TestBillingRouter:
    """Test billing router endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with billing router."""
        app = FastAPI()
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @patch('routers.billing.StripeService.create_checkout_session')
    @patch('routers.billing.get_current_active_user')
    @patch('routers.billing.get_db')
    def test_create_checkout_session_success(
        self, mock_get_db, mock_get_user, mock_create_session, client
    ):
        """Test successful checkout session creation."""
        # Setup mocks
        mock_user = Mock(id=1, organization_id=None)
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        mock_create_session.return_value = "https://checkout.stripe.com/test-session"
        
        # Test request
        response = client.post(
            "/billing/checkout",
            json={
                "plan": "pro",
                "success_url": "https://app.example.com/success",
                "cancel_url": "https://app.example.com/cancel"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://checkout.stripe.com/test-session"
        assert data["plan"] == "pro"
        assert "Checkout session created" in data["message"]
        
        # Verify service was called correctly
        mock_create_session.assert_called_once_with(
            user_id=1,
            tenant_id=None,
            plan="pro",
            success_url="https://app.example.com/success",
            cancel_url="https://app.example.com/cancel",
            db=mock_get_db.return_value
        )
    
    @patch('routers.billing.StripeService.create_checkout_session')
    @patch('routers.billing.get_current_active_user')
    @patch('routers.billing.get_db')
    def test_create_checkout_session_team_plan_with_org(
        self, mock_get_db, mock_get_user, mock_create_session, client
    ):
        """Test team plan checkout with user's organization."""
        # Setup mocks - user has organization
        mock_user = Mock(id=1, organization_id=123)
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        mock_create_session.return_value = "https://checkout.stripe.com/test-session"
        
        # Test request for team plan without explicit tenant_id
        response = client.post(
            "/billing/checkout",
            json={
                "plan": "team",
                "success_url": "https://app.example.com/success",
                "cancel_url": "https://app.example.com/cancel"
            }
        )
        
        # Should succeed using user's organization_id
        assert response.status_code == 200
        
        # Verify service was called with user's organization_id
        mock_create_session.assert_called_once_with(
            user_id=1,
            tenant_id=123,  # Should use user's organization_id
            plan="team",
            success_url="https://app.example.com/success",
            cancel_url="https://app.example.com/cancel",
            db=mock_get_db.return_value
        )
    
    @patch('routers.billing.get_current_active_user')
    @patch('routers.billing.get_db')
    def test_create_checkout_session_team_plan_no_org(
        self, mock_get_db, mock_get_user, client
    ):
        """Test team plan checkout without organization should fail."""
        # Setup mocks - user has no organization
        mock_user = Mock(id=1, organization_id=None)
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        
        # Test request for team plan without tenant_id
        response = client.post(
            "/billing/checkout",
            json={
                "plan": "team",
                "success_url": "https://app.example.com/success",
                "cancel_url": "https://app.example.com/cancel"
            }
        )
        
        # Should fail
        assert response.status_code == 400
        assert "Organization ID required" in response.json()["detail"]
    
    @patch('routers.billing.StripeService.verify_webhook')
    @patch('routers.billing.StripeService.process_event')
    @patch('routers.billing.get_db')
    def test_webhook_success(
        self, mock_get_db, mock_process_event, mock_verify_webhook, client
    ):
        """Test successful webhook processing."""
        # Setup mocks
        mock_event = {"id": "evt_test", "type": "checkout.session.completed"}
        mock_verify_webhook.return_value = mock_event
        mock_process_event.return_value = True
        mock_get_db.return_value = Mock()
        
        # Test webhook request
        response = client.post(
            "/billing/webhook",
            content=json.dumps({"test": "data"}),
            headers={"stripe-signature": "t=1234567890,v1=signature"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["received"] is True
        assert data["processed"] is True
        
        # Verify services were called
        mock_verify_webhook.assert_called_once_with(
            "t=1234567890,v1=signature", 
            json.dumps({"test": "data"}).encode()
        )
        mock_process_event.assert_called_once_with(mock_event, mock_get_db.return_value)
    
    @patch('routers.billing.get_db')
    def test_webhook_missing_signature(self, mock_get_db, client):
        """Test webhook with missing signature header."""
        mock_get_db.return_value = Mock()
        
        # Test webhook request without signature
        response = client.post(
            "/billing/webhook",
            content=json.dumps({"test": "data"})
        )
        
        # Should fail
        assert response.status_code == 400
        assert "Missing Stripe signature" in response.json()["detail"]
    
    @patch('routers.billing.StripeService.verify_webhook')
    @patch('routers.billing.StripeService.process_event')
    @patch('routers.billing.get_db')
    def test_webhook_processing_error(
        self, mock_get_db, mock_process_event, mock_verify_webhook, client
    ):
        """Test webhook processing with error (should still return 200)."""
        # Setup mocks
        mock_event = {"id": "evt_test", "type": "checkout.session.completed"}
        mock_verify_webhook.return_value = mock_event
        mock_process_event.side_effect = Exception("Processing failed")
        mock_get_db.return_value = Mock()
        
        # Test webhook request
        response = client.post(
            "/billing/webhook",
            content=json.dumps({"test": "data"}),
            headers={"stripe-signature": "t=1234567890,v1=signature"}
        )
        
        # Should still return 200 to acknowledge receipt
        assert response.status_code == 200
        data = response.json()
        assert data["received"] is True
        assert data["processed"] is False
        assert "Processing failed" in data["error"]
    
    @patch('routers.billing.EntitlementService.get_current_entitlement')
    @patch('routers.billing.get_current_active_user')
    @patch('routers.billing.get_db')
    def test_get_subscription_status_with_entitlement(
        self, mock_get_db, mock_get_user, mock_get_entitlement, client
    ):
        """Test getting subscription status with active entitlement."""
        # Setup mocks
        mock_user = Mock(id=1, organization_id=123)
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        
        # Create mock entitlement
        mock_entitlement = Mock()
        mock_entitlement.plan = PlanType.PRO
        mock_entitlement.active = True
        mock_entitlement.features = {"api_requests_per_month": 50000}
        mock_entitlement.seats = 5
        mock_entitlement.stripe_customer_id = "cus_test123"
        mock_entitlement.stripe_subscription_id = "sub_test123"
        mock_entitlement.created_at = None
        mock_entitlement.updated_at = None
        
        mock_get_entitlement.return_value = mock_entitlement
        
        # Test request
        response = client.get("/billing/status")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "pro"
        assert data["active"] is True
        assert data["features"] == {"api_requests_per_month": 50000}
        assert data["seats"] == 5
        assert data["stripe_customer_id"] == "cus_test123"
    
    @patch('routers.billing.EntitlementService.get_current_entitlement')
    @patch('routers.billing.get_current_active_user')
    @patch('routers.billing.get_db')
    def test_get_subscription_status_no_entitlement(
        self, mock_get_db, mock_get_user, mock_get_entitlement, client
    ):
        """Test getting subscription status with no entitlement (free plan)."""
        # Setup mocks
        mock_user = Mock(id=1, organization_id=None)
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        mock_get_entitlement.return_value = None
        
        # Test request
        response = client.get("/billing/status")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "free"
        assert data["active"] is True
        assert data["features"] == {}
        assert "No active subscription" in data["message"]
    
    def test_health_check(self, client):
        """Test billing service health check."""
        response = client.get("/billing/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "billing"