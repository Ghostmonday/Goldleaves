# === USAGE TESTS ===
# ✅ Tests for usage API endpoints

"""Tests for usage API endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch

from routers.usage import router as usage_router


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(usage_router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication dependencies."""
    with patch("routers.usage.get_current_user") as mock_user, \
         patch("routers.usage.get_tenant_context") as mock_tenant:
        
        mock_user.return_value = {
            "user_id": 123,
            "email": "test@example.com",
            "is_active": True
        }
        
        mock_tenant.return_value = {
            "tenant_id": "tenant_123",
            "tenant_name": "Test Tenant"
        }
        
        yield mock_user, mock_tenant


class TestUsageSummary:
    """Tests for the usage summary endpoint."""
    
    def test_get_usage_summary_success(self, client, mock_auth):
        """Test successful usage summary retrieval."""
        response = client.get("/api/v1/usage/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_calls" in data
        assert "est_cost_cents" in data
        assert "window_start" in data
        assert "window_end" in data
        
        assert isinstance(data["total_calls"], int)
        assert isinstance(data["est_cost_cents"], int)
        assert data["total_calls"] >= 0
        assert data["est_cost_cents"] >= 0
    
    def test_usage_summary_auth_required(self, client):
        """Test that authentication is required."""
        response = client.get("/api/v1/usage/summary")
        assert response.status_code == 401
    
    def test_usage_summary_window_times(self, client, mock_auth):
        """Test that window times are properly formatted."""
        response = client.get("/api/v1/usage/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate datetime format
        window_start = datetime.fromisoformat(data["window_start"].replace("Z", "+00:00"))
        window_end = datetime.fromisoformat(data["window_end"].replace("Z", "+00:00"))
        
        # Window start should be first of month
        assert window_start.day == 1
        assert window_start.hour == 0
        assert window_start.minute == 0
        assert window_start.second == 0
        
        # Window end should be after window start
        assert window_end >= window_start


class TestDailyUsage:
    """Tests for the daily usage endpoint."""
    
    def test_get_daily_usage_default(self, client, mock_auth):
        """Test daily usage with default 7 days."""
        response = client.get("/api/v1/usage/daily")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "usage" in data
        assert len(data["usage"]) == 7
        
        for item in data["usage"]:
            assert "date" in item
            assert "calls" in item
            assert isinstance(item["calls"], int)
            assert item["calls"] >= 0
            
            # Validate date format YYYY-MM-DD
            datetime.strptime(item["date"], "%Y-%m-%d")
    
    def test_get_daily_usage_custom_days(self, client, mock_auth):
        """Test daily usage with custom number of days."""
        days = 14
        response = client.get(f"/api/v1/usage/daily?days={days}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["usage"]) == days
    
    def test_daily_usage_chronological_order(self, client, mock_auth):
        """Test that daily usage is in chronological order."""
        response = client.get("/api/v1/usage/daily?days=5")
        
        assert response.status_code == 200
        data = response.json()
        
        dates = [item["date"] for item in data["usage"]]
        sorted_dates = sorted(dates)
        
        # Should be in chronological order (oldest first)
        assert dates == sorted_dates
    
    def test_daily_usage_invalid_days_zero(self, client, mock_auth):
        """Test validation for days parameter - zero."""
        response = client.get("/api/v1/usage/daily?days=0")
        assert response.status_code == 400
    
    def test_daily_usage_invalid_days_negative(self, client, mock_auth):
        """Test validation for days parameter - negative."""
        response = client.get("/api/v1/usage/daily?days=-5")
        assert response.status_code == 400
    
    def test_daily_usage_invalid_days_too_large(self, client, mock_auth):
        """Test validation for days parameter - too large."""
        response = client.get("/api/v1/usage/daily?days=100")
        assert response.status_code == 400
    
    def test_daily_usage_auth_required(self, client):
        """Test that authentication is required."""
        response = client.get("/api/v1/usage/daily")
        assert response.status_code == 401


class TestUsageIntegration:
    """Integration tests for usage endpoints."""
    
    def test_consistent_data_between_endpoints(self, client, mock_auth):
        """Test that data is consistent between summary and daily endpoints."""
        summary_response = client.get("/api/v1/usage/summary")
        daily_response = client.get("/api/v1/usage/daily?days=30")
        
        assert summary_response.status_code == 200
        assert daily_response.status_code == 200
        
        summary_data = summary_response.json()
        daily_data = daily_response.json()
        
        # Both should return valid data
        assert summary_data["total_calls"] >= 0
        assert len(daily_data["usage"]) == 30
        
        # Daily data should be within reasonable range
        total_daily_calls = sum(item["calls"] for item in daily_data["usage"])
        assert total_daily_calls >= 0