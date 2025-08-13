"""Test configuration for limits tests."""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from core.entitlements import reset_all_usage


@pytest.fixture(autouse=True)
def reset_usage():
    """Reset usage data before each test."""
    reset_all_usage()
    yield
    reset_all_usage()


@pytest.fixture
def app():
    """Create test app."""
    from routers.main import create_development_app
    return create_development_app()


@pytest.fixture
def client(app):
    """Test client."""
    return TestClient(app)
