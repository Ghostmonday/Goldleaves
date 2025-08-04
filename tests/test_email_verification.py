"""
Comprehensive tests for email verification functionality.
Tests all email verification endpoints including send, confirm, and resend operations.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import jwt

from apps.backend.models import User
from apps.backend.services.auth_service import hash_password
from apps.backend.services.email_verification_service import EmailVerificationService
from core.config import settings


class TestEmailVerificationService:
    """Test the EmailVerificationService directly."""
    
    def test_generate_verification_token(self):
        """✅ Test token generation creates valid JWT."""
        user_id = 123
        token, expires_at = EmailVerificationService.generate_verification_token(user_id)
        
        # Verify token structure
        assert isinstance(token, str)
        assert len(token) > 0
        assert isinstance(expires_at, datetime)
        assert expires_at > datetime.utcnow()
        
        # Decode and verify token content
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm]
        )
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "email_verification"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload
    
    def test_decode_verification_token_valid(self):
        """✅ Test decoding valid verification token."""
        user_id = 456
        token, _ = EmailVerificationService.generate_verification_token(user_id)
        
        payload = EmailVerificationService.decode_verification_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "email_verification"
    
    def test_decode_verification_token_invalid_type(self):
        """❌ Test decoding token with wrong type fails."""
        # Create token with wrong type
        expire = datetime.utcnow() + timedelta(hours=2)
        payload = {
            "sub": "123",
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"  # Wrong type
        }
        token = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)
        
        with pytest.raises(ValueError, match="Invalid token type"):
            EmailVerificationService.decode_verification_token(token)
    
    def test_decode_verification_token_expired(self):
        """❌ Test decoding expired token fails."""
        # Create expired token
        expire = datetime.utcnow() - timedelta(hours=1)
        payload = {
            "sub": "123",
            "exp": expire,
            "iat": datetime.utcnow() - timedelta(hours=2),
            "type": "email_verification"
        }
        token = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)
        
        with pytest.raises(jwt.ExpiredSignatureError):
            EmailVerificationService.decode_verification_token(token)


class TestSendVerificationEndpoint:
    """Test the /auth/verify/send endpoint."""
    
    def test_send_verification_success(self, client: TestClient, db_session: Session):
        """✅ Test successful verification email send."""
        # Create unverified user
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/auth/verify/send",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "verification email sent" in data["message"].lower()
        assert "expires_at" in data
        assert data["expires_at"] is not None
        
        # Verify user has token in database
        db_session.refresh(user)
        assert user.verification_token is not None
        assert user.token_expires_at is not None
        assert user.token_expires_at > datetime.utcnow()
    
    def test_send_verification_user_not_found(self, client: TestClient):
        """❌ Test send verification for non-existent user."""
        response = client.post(
            "/auth/verify/send",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == 400
        assert "User not found" in response.json()["detail"]
    
    def test_send_verification_already_verified(self, client: TestClient, db_session: Session):
        """❌ Test send verification for already verified user."""
        # Create verified user
        user = User(
            username="verified_user",
            email="verified@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/auth/verify/send",
            json={"email": "verified@example.com"}
        )
        
        assert response.status_code == 400
        assert "already verified" in response.json()["detail"].lower()
    
    def test_send_verification_invalid_email(self, client: TestClient):
        """❌ Test send verification with invalid email format."""
        response = client.post(
            "/auth/verify/send",
            json={"email": "invalid-email"}
        )
        
        assert response.status_code == 422  # Pydantic validation error
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
        assert "email" in data["detail"][0]["msg"].lower()
    
    def test_send_verification_missing_email(self, client: TestClient):
        """❌ Test send verification with missing email field."""
        response = client.post("/auth/verify/send", json={})
        
        assert response.status_code == 422  # Pydantic validation error


class TestConfirmVerificationEndpoint:
    """Test the /auth/verify/confirm endpoint."""
    
    def test_confirm_verification_success(self, client: TestClient, db_session: Session):
        """✅ Test successful email verification confirmation."""
        # Create unverified user
        user = User(
            username="confirm_test",
            email="confirm@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Generate verification token
        token, expires_at = EmailVerificationService.generate_verification_token(user.id)
        user.verification_token = token
        user.token_expires_at = expires_at
        db_session.commit()
        
        response = client.post(
            "/auth/verify/confirm",
            json={"token": token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "verified successfully" in data["message"].lower()
        assert data["user_id"] == user.id
        
        # Verify user is now verified in database
        db_session.refresh(user)
        assert user.is_verified is True
        assert user.verification_token is None
        assert user.token_expires_at is None
    
    def test_confirm_verification_invalid_token(self, client: TestClient):
        """❌ Test confirmation with invalid token."""
        response = client.post(
            "/auth/verify/confirm",
            json={"token": "invalid_token"}
        )
        
        assert response.status_code == 401  # Unauthorized for invalid token
        assert "invalid" in response.json()["detail"].lower()
    
    def test_confirm_verification_expired_token(self, client: TestClient, db_session: Session):
        """❌ Test confirmation with expired token."""
        # Create user with expired token
        user = User(
            username="expired_test",
            email="expired@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create expired token
        expire = datetime.utcnow() - timedelta(hours=1)
        payload = {
            "sub": str(user.id),
            "exp": expire,
            "iat": datetime.utcnow() - timedelta(hours=2),
            "type": "email_verification"
        }
        expired_token = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)
        
        user.verification_token = expired_token
        user.token_expires_at = expire
        db_session.commit()
        
        response = client.post(
            "/auth/verify/confirm",
            json={"token": expired_token}
        )
        
        assert response.status_code == 401  # Unauthorized for expired token
        assert "expired" in response.json()["detail"].lower()
    
    def test_confirm_verification_token_mismatch(self, client: TestClient, db_session: Session):
        """❌ Test confirmation when token doesn't match database."""
        # Create user
        user = User(
            username="mismatch_test",
            email="mismatch@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Generate token but store different one in database
        token, expires_at = EmailVerificationService.generate_verification_token(user.id)
        different_token, _ = EmailVerificationService.generate_verification_token(user.id)
        
        user.verification_token = different_token  # Store different token
        user.token_expires_at = expires_at
        db_session.commit()
        
        response = client.post(
            "/auth/verify/confirm",
            json={"token": token}  # Use original token
        )
        
        assert response.status_code == 401  # Unauthorized for mismatched token
        assert "invalid" in response.json()["detail"].lower()
    
    def test_confirm_verification_already_verified(self, client: TestClient, db_session: Session):
        """❌ Test confirmation for already verified user."""
        # Create verified user
        user = User(
            username="already_verified",
            email="already@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Generate token anyway
        token, expires_at = EmailVerificationService.generate_verification_token(user.id)
        user.verification_token = token
        user.token_expires_at = expires_at
        db_session.commit()
        
        response = client.post(
            "/auth/verify/confirm",
            json={"token": token}
        )
        
        assert response.status_code == 200  # Success - already verified users can still verify
        data = response.json()
        assert data["success"] is True
        assert "email already verified" in data["message"].lower()
    
    def test_confirm_verification_missing_token(self, client: TestClient):
        """❌ Test confirmation with missing token field."""
        response = client.post("/auth/verify/confirm", json={})
        
        assert response.status_code == 422  # Pydantic validation error


class TestResendVerificationEndpoint:
    """Test the /auth/verify/resend endpoint."""
    
    def test_resend_verification_success(self, client: TestClient, db_session: Session):
        """✅ Test successful verification email resend."""
        # Create unverified user with old token
        user = User(
            username="resend_test",
            email="resend@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
            is_verified=False,
            verification_token="old_token",
            token_expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(user)
        db_session.commit()
        old_token = user.verification_token
        
        response = client.post(
            "/auth/verify/resend",
            json={"email": "resend@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "verification email resent" in data["message"].lower()
        assert "expires_at" in data
        
        # Verify user has new token in database
        db_session.refresh(user)
        assert user.verification_token is not None
        assert user.verification_token != old_token  # Should be different from old token
        assert user.token_expires_at is not None
        assert user.token_expires_at > datetime.utcnow()
    
    def test_resend_verification_user_not_found(self, client: TestClient):
        """❌ Test resend verification for non-existent user."""
        response = client.post(
            "/auth/verify/resend",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == 400
        assert "User not found" in response.json()["detail"]
    
    def test_resend_verification_already_verified(self, client: TestClient, db_session: Session):
        """❌ Test resend verification for already verified user."""
        # Create verified user
        user = User(
            username="verified_resend",
            email="verified_resend@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/auth/verify/resend",
            json={"email": "verified_resend@example.com"}
        )
        
        assert response.status_code == 400
        assert "already verified" in response.json()["detail"].lower()
    
    def test_resend_verification_invalid_email(self, client: TestClient):
        """❌ Test resend verification with invalid email format."""
        response = client.post(
            "/auth/verify/resend",
            json={"email": "invalid-email"}
        )
        
        assert response.status_code == 422  # Pydantic validation error


class TestEmailVerificationIntegration:
    """Integration tests for email verification flow."""
    
    def test_complete_verification_flow(self, client: TestClient, db_session: Session):
        """✅ Test complete flow from send to confirm."""
        # Create unverified user
        user = User(
            username="integration_test",
            email="integration@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Step 1: Send verification email
        send_response = client.post(
            "/auth/verify/send",
            json={"email": "integration@example.com"}
        )
        
        assert send_response.status_code == 200
        assert send_response.json()["success"] is True
        
        # Get the token from database
        db_session.refresh(user)
        token = user.verification_token
        assert token is not None
        
        # Step 2: Confirm verification
        confirm_response = client.post(
            "/auth/verify/confirm",
            json={"token": token}
        )
        
        assert confirm_response.status_code == 200
        data = confirm_response.json()
        assert data["success"] is True
        assert data["user_id"] == user.id
        
        # Verify final state
        db_session.refresh(user)
        assert user.is_verified is True
        assert user.verification_token is None
    
    def test_resend_and_confirm_flow(self, client: TestClient, db_session: Session):
        """✅ Test resend followed by confirmation."""
        # Create unverified user
        user = User(
            username="resend_confirm_test",
            email="resend_confirm@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Step 1: Send initial verification
        client.post(
            "/auth/verify/send",
            json={"email": "resend_confirm@example.com"}
        )
        
        # Step 2: Resend verification (should generate new token)
        resend_response = client.post(
            "/auth/verify/resend",
            json={"email": "resend_confirm@example.com"}
        )
        
        assert resend_response.status_code == 200
        assert resend_response.json()["success"] is True
        
        # Step 3: Confirm with new token
        db_session.refresh(user)
        new_token = user.verification_token
        
        confirm_response = client.post(
            "/auth/verify/confirm",
            json={"token": new_token}
        )
        
        assert confirm_response.status_code == 200
        assert confirm_response.json()["success"] is True
        
        # Verify final state
        db_session.refresh(user)
        assert user.is_verified is True


class TestResponseSchemaValidation:
    """Test response schemas match expected format."""
    
    def test_send_verification_response_schema(self, client: TestClient, db_session: Session):
        """✅ Test send verification response matches VerificationResponse schema."""
        # Create unverified user
        user = User(
            username="schema_test",
            email="schema@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/auth/verify/send",
            json={"email": "schema@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate required fields
        assert "success" in data
        assert "message" in data
        assert "expires_at" in data
        
        # Validate field types
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)
        assert data["expires_at"] is not None
        
        # Optional token field (development mode)
        if "token" in data:
            assert isinstance(data["token"], str)
    
    def test_confirm_verification_response_schema(self, client: TestClient, db_session: Session):
        """✅ Test confirm verification response matches ConfirmVerificationResponse schema."""
        # Create unverified user with token
        user = User(
            username="confirm_schema",
            email="confirm_schema@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Generate token
        token, expires_at = EmailVerificationService.generate_verification_token(user.id)
        user.verification_token = token
        user.token_expires_at = expires_at
        db_session.commit()
        
        response = client.post(
            "/auth/verify/confirm",
            json={"token": token}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate required fields
        assert "success" in data
        assert "message" in data
        assert "user_id" in data
        
        # Validate field types
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)
        assert isinstance(data["user_id"], int)
        assert data["user_id"] == user.id
    
    def test_error_response_schema(self, client: TestClient):
        """❌ Test error responses match expected format."""
        response = client.post(
            "/auth/verify/send",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == 400
        data = response.json()
        
        # Validate error response structure
        assert "detail" in data
        assert isinstance(data["detail"], str)
