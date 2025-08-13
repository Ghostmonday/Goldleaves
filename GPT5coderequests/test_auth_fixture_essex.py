# tests/fixtures/auth.py
"""Auth fixtures for tests."""
import pytest
from apps.backend.services.auth_service import create_access_token


@pytest.fixture
def auth_token():
    """
    Auth token fixture using auth_service.create_access_token.
    Creates token with user/org ids consistent with middleware expectations.
    """
    # Create token payload with user and organization info
    token_data = {
        "sub": "user123",  # Subject (user identifier)
        "user_id": 123,
        "organization_id": 456,
        "email": "test@example.com",
        "roles": ["user"]
    }
    
    # Create and return token
    token = create_access_token(data=token_data, expires_minutes=30)
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Headers with authorization token."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "X-Organization-ID": "456"
    }


@pytest.fixture
def user_context():
    """User context for testing."""
    return {
        "user_id": 123,
        "organization_id": 456,
        "email": "test@example.com",
        "roles": ["user"]
    }