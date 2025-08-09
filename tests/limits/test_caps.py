"""Tests for plan limits and usage caps functionality."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from routers.middleware import UsageMiddleware
from routers.billing import router as billing_router
from core.entitlements import reset_all_usage, get_usage_info, PLAN_LIMITS


def create_test_app():
    """Create a minimal FastAPI app for testing."""
    app = FastAPI()
    
    # Add the usage middleware
    app.add_middleware(UsageMiddleware)
    
    # Include billing router
    app.include_router(billing_router)
    
    # Add a simple test endpoint
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    return app


@pytest.fixture
def client():
    """Test client with fresh usage data."""
    reset_all_usage()  # Clean slate for each test
    app = create_test_app()
    return TestClient(app)


class TestPlanLimits:
    """Test plan limits and caps enforcement."""
    
    def test_free_plan_limits(self, client):
        """Test Free plan limits are correctly configured."""
        tenant_id = "test_tenant_free"
        
        # Test billing summary for Free plan
        response = client.get(
            "/billing/summary", 
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["plan"] == "Free"
        assert data["unit"] == "api_calls"
        assert data["soft_cap"] == PLAN_LIMITS["Free"]["soft"]
        assert data["hard_cap"] == PLAN_LIMITS["Free"]["hard"]
        assert data["current_usage"] == 0
        assert data["remaining"] == PLAN_LIMITS["Free"]["hard"]
    
    def test_pro_plan_limits(self, client):
        """Test Pro plan limits are correctly configured."""
        tenant_id = "tenant_pro"  # Maps to Pro plan
        
        response = client.get(
            "/billing/summary", 
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["plan"] == "Pro"
        assert data["unit"] == "api_calls"
        assert data["soft_cap"] == PLAN_LIMITS["Pro"]["soft"]
        assert data["hard_cap"] == PLAN_LIMITS["Pro"]["hard"]
    
    def test_team_plan_limits(self, client):
        """Test Team plan limits are correctly configured."""
        tenant_id = "tenant_team"  # Maps to Team plan
        
        response = client.get(
            "/billing/summary", 
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["plan"] == "Team"
        assert data["unit"] == "api_calls"
        assert data["soft_cap"] == PLAN_LIMITS["Team"]["soft"]
        assert data["hard_cap"] == PLAN_LIMITS["Team"]["hard"]


class TestUsageMiddleware:
    """Test usage middleware functionality."""
    
    def test_usage_tracking(self, client):
        """Test that usage is tracked correctly."""
        tenant_id = "test_tenant"
        
        # Make a request to track usage
        response = client.get(
            "/test", 
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 200
        
        # Check usage increased
        usage_info = get_usage_info(tenant_id)
        assert usage_info.current_usage == 1
    
    def test_soft_cap_enforcement(self, client):
        """Test soft cap adds header but allows request."""
        tenant_id = "test_tenant"
        soft_cap = PLAN_LIMITS["Free"]["soft"]  # 500 for Free plan
        
        # Simulate usage at soft cap by making requests
        # Use a more efficient approach by setting usage directly
        from core.entitlements import _usage_storage
        _usage_storage[f"{tenant_id}:api_calls"] = soft_cap - 1
        
        # Make request that should hit soft cap
        response = client.get(
            "/test", 
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 200
        assert "X-Plan-SoftCap" in response.headers
        assert response.headers["X-Plan-SoftCap"] == "true"
    
    def test_hard_cap_enforcement(self, client):
        """Test hard cap blocks request with 429."""
        tenant_id = "test_tenant"
        hard_cap = PLAN_LIMITS["Free"]["hard"]  # 750 for Free plan
        
        # Set usage at hard cap
        from core.entitlements import _usage_storage
        _usage_storage[f"{tenant_id}:api_calls"] = hard_cap
        
        # Make request that should be blocked
        response = client.get(
            "/test", 
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 429
        assert response.json() == {"error": "plan_limit_exceeded"}
    
    def test_near_soft_cap_no_header(self, client):
        """Test that near soft cap (soft-1) has no header and returns 200."""
        tenant_id = "test_tenant"
        soft_cap = PLAN_LIMITS["Free"]["soft"]  # 500 for Free plan
        
        # Set usage to soft cap - 2, then make request to be at soft cap - 1
        from core.entitlements import _usage_storage
        _usage_storage[f"{tenant_id}:api_calls"] = soft_cap - 2
        
        response = client.get(
            "/test", 
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 200
        assert "X-Plan-SoftCap" not in response.headers
    
    def test_billing_summary_consistency(self, client):
        """Test billing summary returns consistent data with usage tracking."""
        tenant_id = "test_tenant"
        
        # Make some requests to generate usage
        for _ in range(5):
            client.get("/test", headers={"X-Tenant-ID": tenant_id})
        
        # Check billing summary
        response = client.get(
            "/billing/summary", 
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["current_usage"] == 5
        assert data["remaining"] == data["hard_cap"] - 5
        assert data["unit"] == "api_calls"
    
    def test_no_behavior_changes_for_other_endpoints(self, client):
        """Test that other behavior is unchanged, only headers/status affected."""
        tenant_id = "test_tenant"
        
        # Make normal request
        response = client.get(
            "/test", 
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "test"}
        
        # Ensure middleware doesn't change response content
        assert "X-Plan-SoftCap" not in response.headers  # Below soft cap
    
    def test_skip_paths_not_tracked(self, client):
        """Test that certain paths skip usage tracking."""
        tenant_id = "test_tenant"
        
        # These should not be tracked
        skip_paths = ["/health", "/docs", "/openapi.json"]
        
        for path in skip_paths:
            response = client.get(path, headers={"X-Tenant-ID": tenant_id})
            # Don't assert status since these endpoints might not exist
            # Just verify no usage was tracked
            
        usage_info = get_usage_info(tenant_id)
        assert usage_info.current_usage == 0


class TestTenantResolution:
    """Test tenant ID resolution from various sources."""
    
    def test_tenant_from_header(self, client):
        """Test tenant ID resolution from X-Tenant-ID header."""
        response = client.get(
            "/billing/summary", 
            headers={"X-Tenant-ID": "test_tenant"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "Free"  # Default plan
    
    def test_no_tenant_id_error(self, client):
        """Test error when no tenant ID is provided."""
        response = client.get("/billing/summary")
        
        assert response.status_code == 400
        assert "No tenant ID found" in response.json()["detail"]
    
    def test_tenant_from_request_state(self, client):
        """Test tenant ID resolution from request state."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from routers.billing import router as billing_router
        
        # Create app with dependency override
        app = FastAPI()
        app.include_router(billing_router)
        
        def mock_get_tenant():
            return "state_tenant"
        
        # Override the dependency
        from routers.billing import get_tenant_id_from_request
        app.dependency_overrides[get_tenant_id_from_request] = mock_get_tenant
        
        test_client = TestClient(app)
        response = test_client.get("/billing/summary")
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])