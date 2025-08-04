"""
Comprehensive test suite for authentication endpoints.
Tests registration, login, token validation, and protected routes.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.backend.main import app
from apps.backend.models import User, RefreshToken
from apps.backend.services.auth_service import (
    create_access_token, 
    hash_password, 
    verify_password,
    decode_token
)
from core.config import settings

client = TestClient(app)

class TestUserRegistration:
    """Test user registration functionality."""
    
    def test_register_user_success(self, client: TestClient, sample_user_data: dict):
        """✅ Test successful user registration with valid data."""
        response = client.post("/auth/register", json=sample_user_data)
        
        # Verify successful registration
        assert response.status_code == 201
        data = response.json()
        
        # Check response structure
        assert "user" in data
        assert "message" in data
        
        # Check user data
        user_data = data["user"]
        assert user_data["username"] == sample_user_data["username"]
        assert user_data["email"] == sample_user_data["email"]
        assert user_data["is_active"] is True
        assert user_data["is_verified"] is False  # Should require verification
        assert "created_at" in user_data
        assert "id" in user_data
        
        # Check message
        assert "registered successfully" in data["message"].lower()
        
        print(f"✅ User registered successfully: {user_data}")

    def test_register_user_duplicate_email(self, client: TestClient, sample_user_data: dict, created_user: User):
        """❌ Test registration fails with duplicate email."""
        # Try to register with email that already exists
        duplicate_data = sample_user_data.copy()
        duplicate_data["email"] = created_user.email
        duplicate_data["username"] = "differentusername"
        
        response = client.post("/auth/register", json=duplicate_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
        
        print(f"✅ Duplicate email registration correctly blocked: {duplicate_data['email']}")

    def test_register_user_duplicate_username(self, client: TestClient, sample_user_data: dict, created_user: User):
        """❌ Test registration fails with duplicate username."""
        # Try to register with username that already exists
        duplicate_data = sample_user_data.copy()
        duplicate_data["username"] = created_user.username
        duplicate_data["email"] = "different@example.com"
        
        response = client.post("/auth/register", json=duplicate_data)
        
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]
        
        print(f"✅ Duplicate username registration correctly blocked: {duplicate_data['username']}")

    def test_register_user_missing_fields(self, client: TestClient):
        """❌ Test registration fails with missing required fields."""
        # Test missing email
        incomplete_data = {
            "username": "testuser",
            "password": "password123"
            # Missing email
        }
        
        response = client.post("/auth/register", json=incomplete_data)
        assert response.status_code == 422  # Validation error
        
        # Test missing username
        incomplete_data = {
            "email": "test@example.com",
            "password": "password123"
            # Missing username
        }
        
        response = client.post("/auth/register", json=incomplete_data)
        assert response.status_code == 422
        
        # Test missing password
        incomplete_data = {
            "username": "testuser",
            "email": "test@example.com"
            # Missing password
        }
        
        response = client.post("/auth/register", json=incomplete_data)
        assert response.status_code == 422
        
        print("✅ Registration correctly validates required fields")

    def test_register_user_invalid_email(self, client: TestClient):
        """❌ Test registration fails with invalid email format."""
        invalid_data = {
            "username": "testuser",
            "email": "invalid-email-format",
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
        print("✅ Registration correctly validates email format")

class TestUserLogin:
    """Test user login functionality."""
    
    def test_login_success(self, client: TestClient, created_user: User):
        """✅ Test successful login with valid credentials."""
        login_data = {
            "email": created_user.email,
            "password": "ExistingPassword789!"  # From fixture
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check token structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["expires_in"] > 0
        
        # Validate JWT token structure
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        
        # Decode and validate access token
        payload = jwt.decode(
            access_token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm]
        )
        
        assert payload["sub"] == str(created_user.id)
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        
        print(f"✅ Login successful. Access token payload: {payload}")
        print(f"✅ Token expires in: {data['expires_in']} seconds")

    def test_login_wrong_email(self, client: TestClient):
        """❌ Test login fails with non-existent email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "anypassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
        
        print("✅ Login correctly rejects non-existent email")

    def test_login_wrong_password(self, client: TestClient, created_user: User):
        """❌ Test login fails with wrong password."""
        login_data = {
            "email": created_user.email,
            "password": "WrongPassword123!"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
        
        print("✅ Login correctly rejects wrong password")

    def test_login_inactive_user(self, client: TestClient, inactive_user: User):
        """❌ Test login fails for inactive user."""
        login_data = {
            "email": inactive_user.email,
            "password": "InactivePassword123!"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Account is inactive" in response.json()["detail"]
        
        print("✅ Login correctly rejects inactive user")

    def test_login_unverified_user_allowed(self, client: TestClient, unverified_user: User):
        """✅ Test login succeeds for unverified user (verification not enforced)."""
        # Note: Email verification is not currently enforced in login
        # This test verifies current behavior - modify if enforcement is added
        
        login_data = {
            "email": unverified_user.email,
            "password": "UnverifiedPassword123!"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        
        print("✅ Login allows unverified users (verification not enforced)")

    def test_login_creates_refresh_token_in_db(self, client: TestClient, created_user: User, db_session: Session):
        """✅ Test login creates refresh token record in database."""
        login_data = {
            "email": created_user.email,
            "password": "ExistingPassword789!"
        }
        
        # Count refresh tokens before login
        tokens_before = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == created_user.id
        ).count()
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        # Count refresh tokens after login
        tokens_after = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == created_user.id
        ).count()
        
        assert tokens_after == tokens_before + 1
        
        # Verify the refresh token exists and is active
        refresh_token = response.json()["refresh_token"]
        db_token = db_session.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()
        
        assert db_token is not None
        assert db_token.is_active is True
        assert db_token.user_id == created_user.id
        assert db_token.expires_at > datetime.utcnow()
        
        print(f"✅ Refresh token stored in database: {db_token.id}")

class TestJWTTokenValidation:
    """Test JWT token structure and validation."""
    
    def test_access_token_structure(self, created_user: User):
        """✅ Test access token has correct structure and expiry."""
        token = create_access_token(created_user.id)
        
        # Decode token
        payload = decode_token(token)
        
        # Verify structure
        assert payload["sub"] == str(created_user.id)
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        
        # Verify expiry is in the future
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        assert exp_datetime > datetime.utcnow()
        
        # Verify expiry is approximately correct (within 1 minute tolerance)
        expected_expiry = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
        time_diff = abs((exp_datetime - expected_expiry).total_seconds())
        assert time_diff < 60  # Within 1 minute
        
        print(f"✅ Access token structure valid. Expires: {exp_datetime}")
        print(f"✅ Token payload: {payload}")

    def test_invalid_token_rejected(self, client: TestClient):
        """❌ Test invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]
        
        print("✅ Invalid tokens correctly rejected")

    def test_expired_token_rejected(self, client: TestClient, created_user: User):
        """❌ Test expired tokens are rejected."""
        # Create an expired token
        expire = datetime.utcnow() - timedelta(minutes=1)  # 1 minute ago
        payload = {
            "sub": str(created_user.id),
            "exp": expire,
            "iat": datetime.utcnow() - timedelta(minutes=2),
            "type": "access"
        }
        expired_token = jwt.encode(
            payload, 
            settings.jwt_secret.get_secret_value(), 
            algorithm=settings.jwt_algorithm
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
        assert "Token expired" in response.json()["detail"]
        
        print("✅ Expired tokens correctly rejected")

class TestProtectedRoutes:
    """Test endpoint protection with access tokens."""
    
    def test_protected_route_requires_token(self, client: TestClient):
        """❌ Test protected route requires valid access token."""
        # Try to access protected route without token
        response = client.get("/auth/me")
        
        assert response.status_code == 403  # No authorization header
        
        print("✅ Protected route correctly requires authentication")

    def test_protected_route_with_valid_token(self, client: TestClient, created_user: User):
        """✅ Test protected route works with valid access token."""
        # Create valid access token
        access_token = create_access_token(created_user.id)
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify user data
        assert data["id"] == created_user.id
        assert data["username"] == created_user.username
        assert data["email"] == created_user.email
        assert data["is_active"] == created_user.is_active
        assert data["is_verified"] == created_user.is_verified
        
        print(f"✅ Protected route accessible with valid token: {data}")

    def test_protected_route_with_wrong_token_type(self, client: TestClient, created_user: User):
        """❌ Test protected route rejects non-access tokens."""
        # Create a refresh-type token
        expire = datetime.utcnow() + timedelta(hours=1)
        payload = {
            "sub": str(created_user.id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"  # Wrong type
        }
        wrong_type_token = jwt.encode(
            payload,
            settings.jwt_secret.get_secret_value(),
            algorithm=settings.jwt_algorithm
        )
        
        headers = {"Authorization": f"Bearer {wrong_type_token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid token type" in response.json()["detail"]
        
        print("✅ Protected route correctly rejects wrong token type")

class TestLogoutFunctionality:
    """Test user logout functionality."""
    
    def test_logout_success(self, client: TestClient, created_user: User, db_session: Session):
        """✅ Test successful logout revokes refresh tokens."""
        # First login to get tokens
        login_data = {
            "email": created_user.email,
            "password": "ExistingPassword789!"
        }
        
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        access_token = login_response.json()["access_token"]
        
        # Verify refresh token exists and is active
        active_tokens_before = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == created_user.id,
            RefreshToken.is_active == True
        ).count()
        assert active_tokens_before > 0
        
        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        logout_response = client.post("/auth/logout", headers=headers)
        
        assert logout_response.status_code == 200
        assert "Logged out successfully" in logout_response.json()["message"]
        
        # Verify all refresh tokens are revoked
        active_tokens_after = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == created_user.id,
            RefreshToken.is_active == True
        ).count()
        assert active_tokens_after == 0
        
        print("✅ Logout successfully revoked all refresh tokens")

    def test_logout_requires_authentication(self, client: TestClient):
        """❌ Test logout requires valid access token."""
        response = client.post("/auth/logout")
        
        assert response.status_code == 403  # No authorization header
        
        print("✅ Logout correctly requires authentication")

class TestIntegrationFlows:
    """Integration tests covering complete user flows."""
    
    def test_complete_registration_login_flow(self, client: TestClient, sample_user_data: dict, db_session: Session):
        """✅ Test complete flow: register → login → access protected route."""
        # Step 1: Register user
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        user_id = register_response.json()["user"]["id"]
        
        # Step 2: Login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        access_token = login_response.json()["access_token"]
        
        # Step 3: Access protected route
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        
        user_data = me_response.json()
        assert user_data["id"] == user_id
        assert user_data["email"] == sample_user_data["email"]
        
        print(f"✅ Complete registration → login → protected access flow successful")

    def test_login_logout_login_flow(self, client: TestClient, created_user: User, db_session: Session):
        """✅ Test login → logout → login again flow."""
        login_data = {
            "email": created_user.email,
            "password": "ExistingPassword789!"
        }
        
        # First login
        login1_response = client.post("/auth/login", json=login_data)
        assert login1_response.status_code == 200
        
        access_token1 = login1_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {access_token1}"}
        logout_response = client.post("/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        
        # Verify old refresh tokens are revoked
        active_tokens = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == created_user.id,
            RefreshToken.is_active == True
        ).count()
        assert active_tokens == 0
        
        # Login again
        login2_response = client.post("/auth/login", json=login_data)
        assert login2_response.status_code == 200
        
        access_token2 = login2_response.json()["access_token"]
        
        # Verify new access token works
        headers2 = {"Authorization": f"Bearer {access_token2}"}
        me_response = client.get("/auth/me", headers=headers2)
        assert me_response.status_code == 200
        
        # Verify new refresh token exists
        active_tokens_after = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == created_user.id,
            RefreshToken.is_active == True
        ).count()
        assert active_tokens_after == 1
        
        print("✅ Login → logout → login flow successful")

class TestResponseSchemaValidation:
    """Test response schemas match expected Pydantic models."""
    
    def test_register_response_schema(self, client: TestClient, sample_user_data: dict):
        """✅ Test register response matches UserResponse schema."""
        response = client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        data = response.json()
        
        # Validate top-level structure
        required_fields = ["user", "message"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Validate user object structure
        user_data = data["user"]
        user_required_fields = ["id", "username", "email", "is_active", "is_verified", "created_at"]
        for field in user_required_fields:
            assert field in user_data, f"Missing user field: {field}"
        
        # Validate data types
        assert isinstance(user_data["id"], int)
        assert isinstance(user_data["username"], str)
        assert isinstance(user_data["email"], str)
        assert isinstance(user_data["is_active"], bool)
        assert isinstance(user_data["is_verified"], bool)
        assert isinstance(user_data["created_at"], str)
        assert isinstance(data["message"], str)
        
        print("✅ Register response schema validation passed")

    def test_login_response_schema(self, client: TestClient, created_user: User):
        """✅ Test login response matches Token schema."""
        login_data = {
            "email": created_user.email,
            "password": "ExistingPassword789!"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate token structure
        required_fields = ["access_token", "refresh_token", "token_type", "expires_in"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Validate data types
        assert isinstance(data["access_token"], str)
        assert isinstance(data["refresh_token"], str)
        assert isinstance(data["token_type"], str)
        assert isinstance(data["expires_in"], int)
        
        # Validate values
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0
        
        print("✅ Login response schema validation passed")

    def test_me_response_schema(self, client: TestClient, created_user: User):
        """✅ Test /me response matches UserRead schema."""
        access_token = create_access_token(created_user.id)
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate structure
        required_fields = ["id", "username", "email", "is_active", "is_verified", "created_at"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Validate data types
        assert isinstance(data["id"], int)
        assert isinstance(data["username"], str)
        assert isinstance(data["email"], str)
        assert isinstance(data["is_active"], bool)
        assert isinstance(data["is_verified"], bool)
        assert isinstance(data["created_at"], str)
        
        # Validate values match user
        assert data["id"] == created_user.id
        assert data["username"] == created_user.username
        assert data["email"] == created_user.email
        assert data["is_active"] == created_user.is_active
        assert data["is_verified"] == created_user.is_verified
        
        print("✅ /me response schema validation passed")

print("🧪 All authentication tests defined and ready for execution!")
print("📋 Coverage includes: Registration, Login, JWT validation, Protected routes, Logout, Integration flows")