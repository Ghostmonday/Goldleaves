"""Tests for health endpoints.

Tests for the health, version, and metrics endpoints to ensure they
return the expected responses and status codes.
"""
import pytest
from fastapi.testclient import TestClient
from routers.health import router
from fastapi import FastAPI


@pytest.fixture
def test_app():
    """Create a test FastAPI app with health router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client."""
    return TestClient(test_app)


def test_health_endpoint_returns_200(test_client):
    """Test that /__health__ endpoint returns 200 status."""
    response = test_client.get("/__health__")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data


def test_version_endpoint_returns_200(test_client):
    """Test that /__version__ endpoint returns 200 status."""
    response = test_client.get("/__version__")
    assert response.status_code == 200
    
    data = response.json()
    assert "version" in data
    assert "git_sha" in data
    assert "environment" in data
    assert "build_time" in data


def test_version_endpoint_with_env_vars(test_client, monkeypatch):
    """Test version endpoint with environment variables set."""
    monkeypatch.setenv("VERSION", "1.2.3")
    monkeypatch.setenv("GIT_SHA", "abc123")
    monkeypatch.setenv("ENVIRONMENT", "test")
    
    response = test_client.get("/__version__")
    assert response.status_code == 200
    
    data = response.json()
    assert data["version"] == "1.2.3"
    assert data["git_sha"] == "abc123"
    assert data["environment"] == "test"


def test_metrics_endpoint_disabled_by_default(test_client):
    """Test that metrics endpoint is disabled by default."""
    response = test_client.get("/metrics")
    assert response.status_code == 404
    assert "disabled" in response.json()["detail"]


def test_metrics_endpoint_enabled(test_client, monkeypatch):
    """Test metrics endpoint when METRICS_ENABLED=true."""
    monkeypatch.setenv("METRICS_ENABLED", "true")
    
    response = test_client.get("/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert "timestamp" in data
    assert "application" in data
    assert "system" in data
    assert data["application"]["name"] == "goldleaves-api"


def test_prometheus_metrics_endpoint_disabled_by_default(test_client):
    """Test that Prometheus metrics endpoint is disabled by default."""
    response = test_client.get("/metrics/prometheus")
    assert response.status_code == 404
    assert "disabled" in response.json()["detail"]


def test_prometheus_metrics_endpoint_enabled(test_client, monkeypatch):
    """Test Prometheus metrics endpoint when METRICS_ENABLED=true."""
    monkeypatch.setenv("METRICS_ENABLED", "true")
    
    response = test_client.get("/metrics/prometheus")
    assert response.status_code == 200
    
    content = response.content.decode()
    assert "goldleaves_info" in content
    assert "goldleaves_up" in content
    assert "# HELP" in content
    assert "# TYPE" in content


def test_health_endpoint_structure(test_client):
    """Test that health endpoint returns all required fields."""
    response = test_client.get("/__health__")
    assert response.status_code == 200
    
    data = response.json()
    required_fields = ["status", "timestamp", "uptime", "version", "environment"]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_version_endpoint_structure(test_client):
    """Test that version endpoint returns all required fields."""
    response = test_client.get("/__version__")
    assert response.status_code == 200
    
    data = response.json()
    required_fields = ["version", "git_sha", "build_time", "environment"]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


@pytest.mark.parametrize("metrics_enabled", ["true", "True", "TRUE", "1"])
def test_metrics_enabled_variations(test_client, monkeypatch, metrics_enabled):
    """Test that metrics endpoint accepts various true values."""
    monkeypatch.setenv("METRICS_ENABLED", metrics_enabled)
    
    response = test_client.get("/metrics")
    assert response.status_code == 200


@pytest.mark.parametrize("metrics_enabled", ["false", "False", "FALSE", "0", ""])
def test_metrics_disabled_variations(test_client, monkeypatch, metrics_enabled):
    """Test that metrics endpoint is disabled for various false values."""
    monkeypatch.setenv("METRICS_ENABLED", metrics_enabled)
    
    response = test_client.get("/metrics")
    assert response.status_code == 404