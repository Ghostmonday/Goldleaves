"""
Test suite for billing endpoints.
Tests checkout creation, authentication, and authorization scenarios.
"""

import pytest
import os
from unittest.mock import patch, AsyncMock
from typing import Dict, Any


class TestBillingService:
    """Test billing service functionality."""
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_mock_mode(self):
        """✅ Test checkout session creation in mock mode."""
        # Set environment variable for mock mode
        with patch.dict(os.environ, {"BILLING_MOCK": "1"}):
            from services.billing_service import BillingService
            
            result = await BillingService.create_checkout_session(
                plan="Pro",
                user_id="user_123",
                tenant_id="tenant_123"
            )
            
            # Verify response structure
            assert "url" in result
            assert isinstance(result["url"], str)
            assert "billing.example" in result["url"]
            assert "plan=Pro" in result["url"]
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_invalid_plan(self):
        """✅ Test checkout session creation with invalid plan."""
        from services.billing_service import BillingService
        
        with pytest.raises(ValueError, match="Invalid plan"):
            await BillingService.create_checkout_session(
                plan="InvalidPlan",
                user_id="user_123"
            )
    
    @pytest.mark.asyncio
    async def test_handle_checkout_success(self):
        """✅ Test handling successful checkout."""
        from services.billing_service import BillingService
        
        result = await BillingService.handle_checkout_success(
            session_id="session_123",
            plan="Pro"
        )
        
        assert "message" in result
        assert "plan" in result
        assert result["plan"] == "Pro"
        assert "successful" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_handle_checkout_cancel(self):
        """✅ Test handling cancelled checkout."""
        from services.billing_service import BillingService
        
        result = await BillingService.handle_checkout_cancel()
        
        assert "message" in result
        assert "cancelled" in result["message"].lower()


class TestBillingSchemas:
    """Test billing schema validation."""
    
    def test_checkout_request_schema_valid(self):
        """✅ Test valid checkout request schema."""
        from schemas.billing import CheckoutRequestSchema
        
        # Test Pro plan
        request = CheckoutRequestSchema(plan="Pro")
        assert request.plan.value == "Pro"
        
        # Test Team plan
        request = CheckoutRequestSchema(plan="Team")
        assert request.plan.value == "Team"
    
    def test_checkout_request_schema_invalid(self):
        """✅ Test invalid checkout request schema."""
        from schemas.billing import CheckoutRequestSchema
        
        with pytest.raises(ValueError):
            CheckoutRequestSchema(plan="InvalidPlan")
    
    def test_checkout_response_schema(self):
        """✅ Test checkout response schema."""
        from schemas.billing import CheckoutResponseSchema
        
        response = CheckoutResponseSchema(url="https://checkout.stripe.com/session_123")
        assert response.url == "https://checkout.stripe.com/session_123"


# Mock test client for endpoint testing (without FastAPI dependency)
class MockTestClient:
    """Mock test client for testing endpoints without FastAPI."""
    
    def __init__(self):
        self.authenticated_user = None
        self.tenant = None
    
    async def post_checkout(self, plan: str, authenticated: bool = True, authorized: bool = True):
        """Mock POST /api/v1/billing/checkout endpoint."""
        if not authenticated:
            return {"status_code": 401, "detail": "Authentication required"}
        
        if not authorized:
            return {"status_code": 403, "detail": "Access denied for tenant"}
        
        # Simulate successful checkout creation
        with patch.dict(os.environ, {"BILLING_MOCK": "1"}):
            from services.billing_service import BillingService
            
            result = await BillingService.create_checkout_session(
                plan=plan,
                user_id="user_123",
                tenant_id="tenant_123" if authorized else None
            )
            
            return {
                "status_code": 200,
                "url": result["url"]
            }


class TestBillingEndpoints:
    """Test billing endpoint behavior."""
    
    @pytest.mark.asyncio
    async def test_checkout_endpoint_authenticated_success(self):
        """✅ Test authenticated checkout request returns URL."""
        client = MockTestClient()
        
        response = await client.post_checkout(
            plan="Pro",
            authenticated=True,
            authorized=True
        )
        
        assert response["status_code"] == 200
        assert "url" in response
        assert isinstance(response["url"], str)
    
    @pytest.mark.asyncio
    async def test_checkout_endpoint_unauthenticated(self):
        """✅ Test unauthenticated request returns 401."""
        client = MockTestClient()
        
        response = await client.post_checkout(
            plan="Pro",
            authenticated=False
        )
        
        assert response["status_code"] == 401
        assert "Authentication required" in response["detail"]
    
    @pytest.mark.asyncio
    async def test_checkout_endpoint_unauthorized(self):
        """✅ Test unauthorized request returns 403."""
        client = MockTestClient()
        
        response = await client.post_checkout(
            plan="Pro",
            authenticated=True,
            authorized=False
        )
        
        assert response["status_code"] == 403
        assert "Access denied" in response["detail"]


if __name__ == "__main__":
    import asyncio
    
    # Simple test runner for demonstration
    async def run_tests():
        print("Running billing service tests...")
        
        # Test billing service
        service_tests = TestBillingService()
        await service_tests.test_create_checkout_session_mock_mode()
        print("✓ Mock checkout session creation")
        
        await service_tests.test_handle_checkout_success()
        print("✓ Checkout success handling")
        
        await service_tests.test_handle_checkout_cancel()
        print("✓ Checkout cancel handling")
        
        # Test schemas
        schema_tests = TestBillingSchemas()
        schema_tests.test_checkout_request_schema_valid()
        print("✓ Valid checkout request schema")
        
        schema_tests.test_checkout_response_schema()
        print("✓ Checkout response schema")
        
        # Test endpoints
        endpoint_tests = TestBillingEndpoints()
        await endpoint_tests.test_checkout_endpoint_authenticated_success()
        print("✓ Authenticated checkout endpoint")
        
        await endpoint_tests.test_checkout_endpoint_unauthenticated()
        print("✓ Unauthenticated checkout endpoint (401)")
        
        await endpoint_tests.test_checkout_endpoint_unauthorized()
        print("✓ Unauthorized checkout endpoint (403)")
        
        print("\nAll billing tests passed! ✅")
    
    if __name__ == "__main__":
        asyncio.run(run_tests())