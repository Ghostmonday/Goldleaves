"""
Test cases for token refresh functionality.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.backend.main import app
from apps.backend.models import User, RefreshToken
from apps.backend.services.auth_service import (
    create_access_token, 
    create_refresh_token, 
    hash_password
)
from core.database import get_db

client = TestClient(app)

def test_refresh_token_success(db_session: Session):
    """Test successful token refresh"""
    # Create a test user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpassword"),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create a refresh token
    refresh_token, expires_at = create_refresh_token(user.id)
    db_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at,
        is_active=True
    )
    db_session.add(db_token)
    db_session.commit()
    
    # Test the refresh endpoint
    response = client.post(
        "/auth/token/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    
    # Verify old token is revoked
    db_session.refresh(db_token)
    assert db_token.is_active == False

def test_refresh_token_invalid(db_session: Session):
    """Test refresh with invalid token"""
    response = client.post(
        "/auth/token/refresh",
        json={"refresh_token": "invalid_token"}
    )
    
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]

def test_refresh_token_expired(db_session: Session):
    """Test refresh with expired token"""
    # Create a test user
    user = User(
        username="testuser2",
        email="test2@example.com",
        hashed_password=hash_password("testpassword"),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create an expired refresh token (use a valid JWT but expired)
    expired_date = datetime.utcnow() - timedelta(days=1)
    
    # Create a properly expired JWT token
    import jwt
    from core.config import settings
    payload = {
        "sub": str(user.id),
        "exp": expired_date,
        "iat": expired_date - timedelta(hours=1),
        "type": "refresh"
    }
    expired_jwt_token = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)
    
    db_token = RefreshToken(
        user_id=user.id,
        token=expired_jwt_token,
        expires_at=expired_date,
        is_active=True
    )
    db_session.add(db_token)
    db_session.commit()
    
    response = client.post(
        "/auth/token/refresh",
        json={"refresh_token": expired_jwt_token}
    )
    
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()

def test_refresh_token_user_not_found(db_session: Session):
    """Test refresh when user doesn't exist"""
    # Create a refresh token for non-existent user
    refresh_token, expires_at = create_refresh_token(99999)
    db_token = RefreshToken(
        user_id=99999,
        token=refresh_token,
        expires_at=expires_at,
        is_active=True
    )
    db_session.add(db_token)
    db_session.commit()
    
    response = client.post(
        "/auth/token/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 401
    assert "User not found" in response.json()["detail"]
