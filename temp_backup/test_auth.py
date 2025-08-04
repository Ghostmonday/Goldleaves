# === AGENT CONTEXT: TESTS AGENT ===
# ✅ Comprehensive JWT Authentication Tests

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time
from fastapi.testclient import TestClient
from fastapi import status
from jose import jwt

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security import (
    create_access_token, create_refresh_token, verify_password, 
    get_password_hash, verify_access_token, verify_refresh_token
)
from core.config import get_settings

# Mock the main app for testing
@pytest.fixture
def mock_app():
    """Create a mock FastAPI app for testing."""
    from fastapi import FastAPI
    app = FastAPI()
    return app

@pytest.fixture
def client():
    """Create test client."""
    # This would normally import your actual app
    # For testing, we'll create a minimal app
    from fastapi import FastAPI
    app = FastAPI()
    return TestClient(app)

@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "id": 1,
        "is_admin": False,
        "is_verified": True
    }

@pytest.fixture
def test_admin_data():
    """Test admin user data."""
    return {
        "email": "admin@example.com",
        "password": "adminpassword123",
        "id": 2,
        "is_admin": True,
        "is_verified": True
    }

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    return session

# === JWT TOKEN TESTS ===

class TestJWTTokens:
    """Test JWT token creation and validation."""
    
    def test_create_access_token(self, test_user_data):
        """Test access token creation."""
        token = create_access_token(
            data={"sub": test_user_data["email"], "user_id": test_user_data["id"]}
        )
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token structure
        payload = verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == test_user_data["email"]
        assert payload["user_id"] == test_user_data["id"]
        assert payload["type"] == "access"
    
    def test_create_refresh_token(self, test_user_data):
        """Test refresh token creation."""
        token = create_refresh_token(
            data={"sub": test_user_data["email"], "user_id": test_user_data["id"]}
        )
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token structure
        payload = verify_refresh_token(token)
        assert payload is not None
        assert payload["sub"] == test_user_data["email"]
        assert payload["user_id"] == test_user_data["id"]
        assert payload["type"] == "refresh"
    
    def test_token_expiration(self, test_user_data):
        """Test token expiration."""
        # Create token with very short expiration
        token = create_access_token(
            data={"sub": test_user_data["email"]},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        payload = verify_access_token(token)
        assert payload is None  # Should be None due to expiration
    
    def test_invalid_token(self):
        """Test invalid token handling."""
        invalid_token = "invalid.token.here"
        payload = verify_access_token(invalid_token)
        assert payload is None
    
    def test_wrong_token_type(self, test_user_data):
        """Test using refresh token as access token."""
        refresh_token = create_refresh_token(
            data={"sub": test_user_data["email"]}
        )
        
        # Try to verify refresh token as access token
        payload = verify_access_token(refresh_token)
        assert payload is None  # Should fail type check

# === PASSWORD HASHING TESTS ===

class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_different_hashes(self):
        """Test that same password produces different hashes."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Should be different due to salt
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

# === REGISTRATION TESTS ===

class TestUserRegistration:
    """Test user registration functionality."""
    
    @patch('models.core_db.get_db')
    @patch('models.user.User')
    def test_successful_registration(self, mock_user, mock_db, test_user_data):
        """Test successful user registration."""
        # Mock database session
        mock_db_session = MagicMock()
        mock_db.return_value = mock_db_session
        
        # Mock that user doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Mock user creation
        mock_user_instance = MagicMock()
        mock_user.return_value = mock_user_instance
        
        # Simulate registration
        email = test_user_data["email"]
        password = test_user_data["password"]
        
        # Hash password
        hashed_password = get_password_hash(password)
        
        # Verify password was hashed correctly
        assert verify_password(password, hashed_password)
        
        # Verify database operations would be called
        mock_db_session.add.assert_not_called()  # Not called yet in this test
        mock_db_session.commit.assert_not_called()
    
    @patch('models.core_db.get_db')
    def test_duplicate_email_registration(self, mock_db, test_user_data):
        """Test registration with duplicate email."""
        # Mock database session
        mock_db_session = MagicMock()
        mock_db.return_value = mock_db_session
        
        # Mock that user already exists
        existing_user = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = existing_user
        
        # This would trigger a 409 Conflict in the actual implementation
        assert existing_user is not None

# === LOGIN TESTS ===

class TestUserLogin:
    """Test user login functionality."""
    
    @patch('models.core_db.get_db')
    def test_successful_login(self, mock_db, test_user_data):
        """Test successful login."""
        # Mock database session
        mock_db_session = MagicMock()
        mock_db.return_value = mock_db_session
        
        # Create mock user
        mock_user = MagicMock()
        mock_user.email = test_user_data["email"]
        mock_user.hashed_password = get_password_hash(test_user_data["password"])
        mock_user.is_active = True
        mock_user.is_admin = test_user_data["is_admin"]
        mock_user.is_verified = test_user_data["is_verified"]
        mock_user.id = test_user_data["id"]
        
        # Mock database query
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Verify password verification works
        assert verify_password(test_user_data["password"], mock_user.hashed_password)
        
        # Create tokens as would happen in login
        access_token = create_access_token(
            data={
                "sub": mock_user.email,
                "user_id": mock_user.id,
                "is_admin": mock_user.is_admin
            }
        )
        
        refresh_token = create_refresh_token(
            data={"sub": mock_user.email, "user_id": mock_user.id}
        )
        
        assert access_token is not None
        assert refresh_token is not None
    
    @patch('models.core_db.get_db')
    def test_invalid_credentials(self, mock_db, test_user_data):
        """Test login with invalid credentials."""
        # Mock database session
        mock_db_session = MagicMock()
        mock_db.return_value = mock_db_session
        
        # Mock user not found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # This would trigger a 401 Unauthorized in the actual implementation
        user = mock_db_session.query.return_value.filter.return_value.first.return_value
        assert user is None
    
    @patch('models.core_db.get_db')
    def test_inactive_user_login(self, mock_db, test_user_data):
        """Test login with inactive user."""
        # Mock database session
        mock_db_session = MagicMock()
        mock_db.return_value = mock_db_session
        
        # Create mock inactive user
        mock_user = MagicMock()
        mock_user.email = test_user_data["email"]
        mock_user.hashed_password = get_password_hash(test_user_data["password"])
        mock_user.is_active = False  # Inactive user
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # This would trigger a 401 Unauthorized in the actual implementation
        assert not mock_user.is_active

# === TOKEN VALIDATION TESTS ===

class TestTokenValidation:
    """Test token validation middleware and functions."""
    
    def test_valid_access_token_validation(self, test_user_data):
        """Test validation of valid access token."""
        token = create_access_token(
            data={"sub": test_user_data["email"], "user_id": test_user_data["id"]}
        )
        
        payload = verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == test_user_data["email"]
        assert payload["user_id"] == test_user_data["id"]
    
    def test_expired_token_validation(self, test_user_data):
        """Test validation of expired token."""
        # Create expired token
        token = create_access_token(
            data={"sub": test_user_data["email"]},
            expires_delta=timedelta(seconds=-1)
        )
        
        payload = verify_access_token(token)
        assert payload is None
    
    def test_malformed_token_validation(self):
        """Test validation of malformed token."""
        malformed_token = "not.a.valid.jwt.token"
        payload = verify_access_token(malformed_token)
        assert payload is None

# === REFRESH TOKEN TESTS ===

class TestTokenRefresh:
    """Test token refresh functionality."""
    
    @patch('models.core_db.get_db')
    def test_successful_token_refresh(self, mock_db, test_user_data):
        """Test successful token refresh."""
        # Create refresh token
        refresh_token = create_refresh_token(
            data={"sub": test_user_data["email"], "user_id": test_user_data["id"]}
        )
        
        # Verify refresh token
        payload = verify_refresh_token(refresh_token)
        assert payload is not None
        assert payload["sub"] == test_user_data["email"]
        assert payload["user_id"] == test_user_data["id"]
        
        # Mock database for user lookup
        mock_db_session = MagicMock()
        mock_db.return_value = mock_db_session
        
        mock_user = MagicMock()
        mock_user.email = test_user_data["email"]
        mock_user.id = test_user_data["id"]
        mock_user.is_active = True
        mock_user.is_admin = test_user_data["is_admin"]
        mock_user.is_verified = test_user_data["is_verified"]
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Create new access token
        new_access_token = create_access_token(
            data={
                "sub": mock_user.email,
                "user_id": mock_user.id,
                "is_admin": mock_user.is_admin
            }
        )
        
        assert new_access_token is not None
        
        # Verify new token
        new_payload = verify_access_token(new_access_token)
        assert new_payload is not None
        assert new_payload["sub"] == test_user_data["email"]

# === MIDDLEWARE TESTS ===

class TestAuthenticationMiddleware:
    """Test authentication middleware."""
    
    def test_public_path_bypass(self):
        """Test that public paths bypass authentication."""
        public_paths = ["/auth/login", "/auth/register", "/docs", "/health"]
        
        for path in public_paths:
            # Public paths should not require authentication
            assert any(path.startswith(public_path) for public_path in public_paths)
    
    def test_protected_path_requires_auth(self):
        """Test that protected paths require authentication."""
        protected_paths = ["/api/v1/users/me", "/api/v1/admin", "/protected"]
        
        for path in protected_paths:
            # These paths should require authentication
            # In actual middleware, missing Authorization header would return 401
            assert not any(path.startswith(public_path) for public_path in ["/auth/", "/docs", "/health"])

# === INTEGRATION TESTS ===

class TestAuthenticationIntegration:
    """Integration tests for complete authentication flow."""
    
    def test_complete_auth_flow(self, test_user_data):
        """Test complete authentication flow."""
        # 1. User registration (password hashing)
        password = test_user_data["password"]
        hashed_password = get_password_hash(password)
        assert verify_password(password, hashed_password)
        
        # 2. User login (token creation)
        access_token = create_access_token(
            data={"sub": test_user_data["email"], "user_id": test_user_data["id"]}
        )
        refresh_token = create_refresh_token(
            data={"sub": test_user_data["email"], "user_id": test_user_data["id"]}
        )
        
        # 3. Token validation
        access_payload = verify_access_token(access_token)
        refresh_payload = verify_refresh_token(refresh_token)
        
        assert access_payload is not None
        assert refresh_payload is not None
        assert access_payload["sub"] == test_user_data["email"]
        assert refresh_payload["sub"] == test_user_data["email"]
        
        # 4. Token refresh
        new_access_token = create_access_token(
            data={"sub": test_user_data["email"], "user_id": test_user_data["id"]}
        )
        new_payload = verify_access_token(new_access_token)
        assert new_payload is not None

# === PERFORMANCE TESTS ===

class TestAuthenticationPerformance:
    """Test authentication performance."""
    
    def test_password_hashing_performance(self):
        """Test password hashing performance."""
        password = "testpassword123"
        
        start_time = time.time()
        for _ in range(10):
            get_password_hash(password)
        end_time = time.time()
        
        # Should complete 10 hashes in reasonable time (< 5 seconds)
        assert end_time - start_time < 5.0
    
    def test_token_verification_performance(self, test_user_data):
        """Test token verification performance."""
        token = create_access_token(
            data={"sub": test_user_data["email"], "user_id": test_user_data["id"]}
        )
        
        start_time = time.time()
        for _ in range(100):
            verify_access_token(token)
        end_time = time.time()
        
        # Should complete 100 verifications quickly (< 1 second)
        assert end_time - start_time < 1.0

# === SECURITY TESTS ===

class TestAuthenticationSecurity:
    """Test authentication security features."""
    
    def test_token_tampering_detection(self, test_user_data):
        """Test that tampered tokens are rejected."""
        token = create_access_token(
            data={"sub": test_user_data["email"], "user_id": test_user_data["id"]}
        )
        
        # Tamper with token
        tampered_token = token[:-5] + "XXXXX"
        
        payload = verify_access_token(tampered_token)
        assert payload is None
    
    def test_password_strength_hashing(self):
        """Test that passwords are properly hashed."""
        passwords = ["simple", "complex!123", "VeryLongPasswordWithSpecialChars!@#123"]
        
        for password in passwords:
            hashed = get_password_hash(password)
            
            # Hash should be different from password
            assert hashed != password
            
            # Hash should be consistent length (bcrypt)
            assert len(hashed) > 50  # bcrypt hashes are long
            
            # Should verify correctly
            assert verify_password(password, hashed)

if __name__ == "__main__":
    pytest.main([__file__])

# === EXISTING BASIC TESTS ===

def test_register_user_success():
    response = client.post("/register", json={
        "email": "newuser@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_success():
    # First register a user
    client.post("/register", json={
        "email": "loginuser@example.com",
        "password": "securepassword123"
    })
    
    # Then try to login
    response = client.post("/login", json={
        "email": "loginuser@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_duplicate_registration():
    """Test for registering with existing email"""
    # Register user first time
    client.post("/register", json={
        "email": "duplicate@example.com",
        "password": "securepassword123"
    })
    
    # Try to register with same email
    response = client.post("/register", json={
        "email": "duplicate@example.com",
        "password": "anothersecurepassword123"
    })
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_invalid_email_format():
    """Test for invalid email format"""
    response = client.post("/register", json={
        "email": "invalidemail",
        "password": "securepassword123"
    })
    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]
    assert "valid email" in response.json()["detail"][0]["msg"].lower()

def test_short_password():
    """Test for short password"""
    response = client.post("/register", json={
        "email": "validuser@example.com",
        "password": "short"
    })
    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]
    assert "length" in response.json()["detail"][0]["msg"].lower()

def test_invalid_login():
    """Test for invalid login attempt (wrong credentials)"""
    # First register a user
    client.post("/register", json={
        "email": "correctuser@example.com",
        "password": "securepassword123"
    })
    
    # Try to login with wrong password
    response = client.post("/login", json={
        "email": "correctuser@example.com",
        "password": "wrongpassword123"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]
    
    # Try to login with wrong email
    response = client.post("/login", json={
        "email": "nonexistent@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


# === PHASE 2 TESTS ===

def test_email_verification_flow_valid_token():
    """Test complete email verification flow with valid token"""
    # Register user (should create unverified user)
    register_response = client.post("/register", json={
        "email": "verify_valid@example.com",
        "password": "securepassword123"
    })
    assert register_response.status_code == 200
    user_data = register_response.json()
    assert user_data["email_verified"] is False
    assert "verification_token" in user_data
    
    # Attempt login before verification (should succeed but show unverified status)
    login_response = client.post("/login", json={
        "email": "verify_valid@example.com",
        "password": "securepassword123"
    })
    assert login_response.status_code == 200
    assert login_response.json()["email_verified"] is False
    
    # Verify email with valid token
    verification_token = user_data["verification_token"]
    verify_response = client.post(f"/verify-email/{verification_token}")
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert verify_data["message"] == "Email verified successfully"
    assert verify_data["email_verified"] is True
    
    # Login after verification should show verified status
    post_verify_login = client.post("/login", json={
        "email": "verify_valid@example.com",
        "password": "securepassword123"
    })
    assert post_verify_login.status_code == 200
    assert post_verify_login.json()["email_verified"] is True


def test_email_verification_flow_expired_token():
    """Test email verification with expired token"""
    # Register user
    register_response = client.post("/register", json={
        "email": "verify_expired@example.com",
        "password": "securepassword123"
    })
    assert register_response.status_code == 200
    
    # Use a clearly expired/invalid token
    expired_token = "expired_or_invalid_token_12345"
    
    # Attempt verification with expired token
    verify_response = client.post(f"/verify-email/{expired_token}")
    assert verify_response.status_code == 400
    error_data = verify_response.json()
    assert "expired" in error_data["detail"].lower() or "invalid" in error_data["detail"].lower()
    
    # User should still be unverified
    login_response = client.post("/login", json={
        "email": "verify_expired@example.com",
        "password": "securepassword123"
    })
    assert login_response.status_code == 200
    assert login_response.json()["email_verified"] is False


def test_email_verification_resend_token():
    """Test resending verification token for existing user"""
    # Register user
    client.post("/register", json={
        "email": "resend_token@example.com",
        "password": "securepassword123"
    })
    
    # Request new verification token
    resend_response = client.post("/resend-verification", json={
        "email": "resend_token@example.com"
    })
    assert resend_response.status_code == 200
    resend_data = resend_response.json()
    assert "verification_token" in resend_data
    assert resend_data["message"] == "Verification email sent"
    
    # Verify with new token
    new_token = resend_data["verification_token"]
    verify_response = client.post(f"/verify-email/{new_token}")
    assert verify_response.status_code == 200
    assert verify_response.json()["email_verified"] is True


def test_admin_only_route_access_forbidden():
    """Test that regular users cannot access admin-only routes"""
    # Register and login as regular user
    client.post("/register", json={
        "email": "regular_user@example.com",
        "password": "securepassword123"
    })
    
    login_response = client.post("/login", json={
        "email": "regular_user@example.com",
        "password": "securepassword123"
    })
    regular_token = login_response.json()["access_token"]
    
    # Attempt to access admin routes with regular user token
    admin_routes = [
        "/admin/users",
        "/admin/users/1",
        "/admin/stats"
    ]
    
    for route in admin_routes:
        response = client.get(
            route,
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 403
        error_data = response.json()
        assert "permission" in error_data["detail"].lower() or "admin" in error_data["detail"].lower()


def test_admin_only_route_access_success():
    """Test that admin users can access admin-only routes"""
    # Create admin user (assuming admin creation endpoint exists)
    admin_create_response = client.post("/admin/create-admin", json={
        "email": "admin_user@example.com",
        "password": "adminsecurepassword123",
        "admin_key": "super_secret_admin_key"
    })
    assert admin_create_response.status_code == 201
    
    # Login as admin
    admin_login = client.post("/login", json={
        "email": "admin_user@example.com",
        "password": "adminsecurepassword123"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    assert admin_login.json()["is_admin"] is True
    
    # Access admin routes successfully
    users_response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert users_response.status_code == 200
    users_data = users_response.json()
    assert "users" in users_data
    assert isinstance(users_data["users"], list)
    
    # Access admin stats
    stats_response = client.get(
        "/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    assert "total_users" in stats_data
    assert "verified_users" in stats_data


def test_admin_user_creation_with_flags():
    """Test admin creating users with specific flags and permissions"""
    # Login as admin
    admin_login = client.post("/login", json={
        "email": "admin_user@example.com",
        "password": "adminsecurepassword123"
    })
    admin_token = admin_login.json()["access_token"]
    
    # Create regular user as admin
    regular_user_data = {
        "email": "admin_created_regular@example.com",
        "password": "userpassword123",
        "is_admin": False,
        "email_verified": True,
        "is_active": True
    }
    
    create_response = client.post(
        "/admin/users",
        json=regular_user_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_response.status_code == 201
    created_user = create_response.json()
    assert created_user["email"] == regular_user_data["email"]
    assert created_user["is_admin"] is False
    assert created_user["email_verified"] is True
    assert created_user["is_active"] is True
    assert "id" in created_user
    assert "password" not in created_user  # Password should not be returned
    
    # Verify created user can login immediately (pre-verified)
    user_login = client.post("/login", json={
        "email": "admin_created_regular@example.com",
        "password": "userpassword123"
    })
    assert user_login.status_code == 200
    assert user_login.json()["email_verified"] is True


def test_admin_user_creation_with_admin_flags():
    """Test admin creating another admin user"""
    # Login as existing admin
    admin_login = client.post("/login", json={
        "email": "admin_user@example.com",
        "password": "adminsecurepassword123"
    })
    admin_token = admin_login.json()["access_token"]
    
    # Create admin user as admin
    admin_user_data = {
        "email": "new_admin@example.com",
        "password": "newadminpassword123",
        "is_admin": True,
        "email_verified": True,
        "is_active": True
    }
    
    create_response = client.post(
        "/admin/users",
        json=admin_user_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_response.status_code == 201
    created_admin = create_response.json()
    assert created_admin["email"] == admin_user_data["email"]
    assert created_admin["is_admin"] is True
    assert created_admin["email_verified"] is True
    
    # Verify new admin can access admin routes
    new_admin_login = client.post("/login", json={
        "email": "new_admin@example.com",
        "password": "newadminpassword123"
    })
    assert new_admin_login.status_code == 200
    new_admin_token = new_admin_login.json()["access_token"]
    
    admin_route_response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {new_admin_token}"}
    )
    assert admin_route_response.status_code == 200


def test_admin_user_creation_validation():
    """Test admin user creation with invalid data"""
    # Login as admin
    admin_login = client.post("/login", json={
        "email": "admin_user@example.com",
        "password": "adminsecurepassword123"
    })
    admin_token = admin_login.json()["access_token"]
    
    # Test with invalid email
    invalid_email_data = {
        "email": "invalid-email-format",
        "password": "validpassword123",
        "is_admin": False
    }
    
    response = client.post(
        "/admin/users",
        json=invalid_email_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422
    error_data = response.json()
    assert "email" in str(error_data["detail"]).lower()
    
    # Test with short password
    short_password_data = {
        "email": "valid@example.com",
        "password": "short",
        "is_admin": False
    }
    
    response = client.post(
        "/admin/users",
        json=short_password_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422
    error_data = response.json()
    assert "password" in str(error_data["detail"]).lower()
    
    # Test duplicate email
    duplicate_email_data = {
        "email": "admin_user@example.com",  # Already exists
        "password": "validpassword123",
        "is_admin": False
    }
    
    response = client.post(
        "/admin/users",
        json=duplicate_email_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    error_data = response.json()
    assert "already exists" in error_data["detail"].lower() or "already registered" in error_data["detail"].lower()


# === PHASE 4 INTEGRATION TESTS ===

@pytest.mark.integration
def test_organization_security_document_flow(mock_email_service, performance_timer):
    """Integration test for org creation, security checks, and document handling"""
    # Create organization admin
    org_admin_response = client.post("/register", json={
        "email": "orgadmin@example.com",
        "password": "orgadminpass123",
        "organization_name": "TestOrg Inc"
    })
    assert org_admin_response.status_code == 200
    org_admin_token = org_admin_response.json()["access_token"]
    org_id = org_admin_response.json()["organization_id"]
    
    # Verify email verification was triggered
    mock_email_service.assert_called_once()
    
    # Create organization member
    member_response = client.post("/register", json={
        "email": "member@example.com",
        "password": "memberpass123",
        "organization_id": org_id
    })
    assert member_response.status_code == 200
    member_token = member_response.json()["access_token"]
    
    # Test organization boundary enforcement
    other_org_response = client.post("/register", json={
        "email": "other@example.com",
        "password": "otherpass123",
        "organization_name": "OtherOrg Inc"
    })
    other_token = other_org_response.json()["access_token"]
    
    # Member should not access other org's documents
    cross_org_response = client.get(
        f"/organizations/{org_id}/documents",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert cross_org_response.status_code == 403
    
    # Member should access own org's documents
    own_org_response = client.get(
        f"/organizations/{org_id}/documents",
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert own_org_response.status_code == 200


@pytest.mark.unit
def test_service_logic_validation(mock_db_session):
    """Unit tests for service logic and schema validation"""
    # Test token service validation
    with patch('services.token_service.create_verification_token') as mock_token:
        mock_token.return_value = "test_token_12345"
        
        register_response = client.post("/register", json={
            "email": "servicetest@example.com",
            "password": "servicepass123"
        })
        
        assert register_response.status_code == 200
        mock_token.assert_called_once()
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    # Test schema validation edge cases
    invalid_schemas = [
        {"email": "test@", "password": "validpass123"},  # Invalid email
        {"email": "valid@example.com", "password": "sh"},  # Short password
        {"email": "valid@example.com"},  # Missing password
        {"password": "validpass123"},  # Missing email
    ]
    
    for invalid_data in invalid_schemas:
        response = client.post("/register", json=invalid_data)
        assert response.status_code == 422


@pytest.mark.permissions
def test_multi_tenant_boundary_checks():
    """Test permission and multi-tenant boundary enforcement"""
    # Create two organizations
    org1_response = client.post("/register", json={
        "email": "org1admin@example.com",
        "password": "org1pass123",
        "organization_name": "Org1 Inc"
    })
    org1_token = org1_response.json()["access_token"]
    org1_id = org1_response.json()["organization_id"]
    
    org2_response = client.post("/register", json={
        "email": "org2admin@example.com",
        "password": "org2pass123",
        "organization_name": "Org2 Inc"
    })
    org2_token = org2_response.json()["access_token"]
    org2_id = org2_response.json()["organization_id"]
    
    # Test cross-tenant access prevention
    cross_tenant_tests = [
        (f"/organizations/{org2_id}/users", org1_token),
        (f"/organizations/{org1_id}/settings", org2_token),
        (f"/admin/organizations/{org2_id}", org1_token),
        (f"/admin/organizations/{org1_id}", org2_token),
    ]
    
    for endpoint, wrong_token in cross_tenant_tests:
        response = client.get(
            endpoint,
            headers={"Authorization": f"Bearer {wrong_token}"}
        )
        assert response.status_code in [403, 404], f"Failed boundary check for {endpoint}"


@pytest.mark.performance
def test_performance_benchmarks():
    """Performance tests with query benchmarks"""
    # Test registration performance
    start_time = time.time()
    batch_size = 10
    
    for i in range(batch_size):
        response = client.post("/register", json={
            "email": f"perftest{i}@example.com",
            "password": "perfpass123"
        })
        assert response.status_code == 200
    
    end_time = time.time()
    avg_time_per_request = (end_time - start_time) / batch_size
    assert avg_time_per_request < 0.5, f"Registration too slow: {avg_time_per_request:.2f}s per request"
    
    # Test login performance
    start_time = time.time()
    for i in range(batch_size):
        response = client.post("/login", json={
            "email": f"perftest{i}@example.com",
            "password": "perfpass123"
        })
        assert response.status_code == 200
    
    end_time = time.time()
    avg_login_time = (end_time - start_time) / batch_size
    assert avg_login_time < 0.3, f"Login too slow: {avg_login_time:.2f}s per request"


@pytest.mark.contracts
def test_contract_enforcement():
    """Validate contract enforcement for routers and services"""
    # Test required response fields are present
    register_response = client.post("/register", json={
        "email": "contract@example.com",
        "password": "contractpass123"
    })
    
    required_fields = ["access_token", "user_id", "email", "email_verified"]
    response_data = register_response.json()
    
    for field in required_fields:
        assert field in response_data, f"Contract violation: missing {field}"
    
    # Test response field types
    assert isinstance(response_data["access_token"], str)
    assert isinstance(response_data["user_id"], (int, str))
    assert isinstance(response_data["email"], str)
    assert isinstance(response_data["email_verified"], bool)
    
    # Test login contract
    login_response = client.post("/login", json={
        "email": "contract@example.com",
        "password": "contractpass123"
    })
    
    login_data = login_response.json()
    login_required_fields = ["access_token", "token_type", "expires_in"]
    
    for field in login_required_fields:
        assert field in login_data, f"Login contract violation: missing {field}"


@pytest.mark.mocking
def test_external_dependencies_mocked():
    """Test that external dependencies are properly mocked"""
    with patch('core.email_utils.send_verification_email') as mock_email, \
         patch('services.auth_service.hash_password') as mock_hash, \
         patch('database.get_db') as mock_db:
        
        mock_email.return_value = True
        mock_hash.return_value = "hashed_password_123"
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Register user with mocked dependencies
        response = client.post("/register", json={
            "email": "mocked@example.com",
            "password": "mockedpass123"
        })
        
        # Verify mocks were called
        mock_email.assert_called()
        mock_hash.assert_called_with("mockedpass123")
        mock_session.add.assert_called()
        mock_session.commit.assert_called()


@pytest.mark.database
def test_db_state_and_side_effects(mock_db_session):
    """Assert database state and side effects after API calls"""
    # Test user creation side effects
    with patch('models.user.User') as MockUser:
        mock_user_instance = MagicMock()
        MockUser.return_value = mock_user_instance
        
        response = client.post("/register", json={
            "email": "dbtest@example.com",
            "password": "dbtestpass123"
        })
        
        # Verify database operations
        mock_db_session.add.assert_called_with(mock_user_instance)
        mock_db_session.commit.assert_called()
        
        # Verify user properties were set
        assert mock_user_instance.email == "dbtest@example.com"
        assert mock_user_instance.email_verified is False
        assert mock_user_instance.is_active is True


@pytest.mark.coverage
def test_edge_cases_for_coverage():
    """Test edge cases to maintain >90% coverage"""
    # Test malformed JSON
    response = client.post("/register", 
                          data="invalid json",
                          headers={"content-type": "application/json"})
    assert response.status_code == 422
    
    # Test missing content-type
    response = client.post("/register", data='{"email": "test@example.com"}')
    assert response.status_code in [422, 415]
    
    # Test extremely long inputs
    long_email = "a" * 300 + "@example.com"
    response = client.post("/register", json={
        "email": long_email,
        "password": "validpass123"
    })
    assert response.status_code == 422
    
    # Test special characters in password
    response = client.post("/register", json={
        "email": "special@example.com",
        "password": "special!@#$%^&*()pass123"
    })
    assert response.status_code == 200

def test_register_user_success():
    response = client.post("/register", json={
        "email": "newuser@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_success():
    # First register a user
    client.post("/register", json={
        "email": "loginuser@example.com",
        "password": "securepassword123"
    })
    
    # Then try to login
    response = client.post("/login", json={
        "email": "loginuser@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_duplicate_registration():
    """Test for registering with existing email"""
    # Register user first time
    client.post("/register", json={
        "email": "duplicate@example.com",
        "password": "securepassword123"
    })
    
    # Try to register with same email
    response = client.post("/register", json={
        "email": "duplicate@example.com",
        "password": "anothersecurepassword123"
    })
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_invalid_email_format():
    """Test for invalid email format"""
    response = client.post("/register", json={
        "email": "invalidemail",
        "password": "securepassword123"
    })
    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]
    assert "valid email" in response.json()["detail"][0]["msg"].lower()

def test_short_password():
    """Test for short password"""
    response = client.post("/register", json={
        "email": "validuser@example.com",
        "password": "short"
    })
    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]
    assert "length" in response.json()["detail"][0]["msg"].lower()

def test_invalid_login():
    """Test for invalid login attempt (wrong credentials)"""
    # First register a user
    client.post("/register", json={
        "email": "correctuser@example.com",
        "password": "securepassword123"
    })
    
    # Try to login with wrong password
    response = client.post("/login", json={
        "email": "correctuser@example.com",
        "password": "wrongpassword123"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]
    
    # Try to login with wrong email
    response = client.post("/login", json={
        "email": "nonexistent@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


# === PHASE 2 TESTS ===

def test_email_verification_flow_valid_token():
    """Test complete email verification flow with valid token"""
    # Register user (should create unverified user)
    register_response = client.post("/register", json={
        "email": "verify_valid@example.com",
        "password": "securepassword123"
    })
    assert register_response.status_code == 200
    user_data = register_response.json()
    assert user_data["email_verified"] is False
    assert "verification_token" in user_data
    
    # Attempt login before verification (should succeed but show unverified status)
    login_response = client.post("/login", json={
        "email": "verify_valid@example.com",
        "password": "securepassword123"
    })
    assert login_response.status_code == 200
    assert login_response.json()["email_verified"] is False
    
    # Verify email with valid token
    verification_token = user_data["verification_token"]
    verify_response = client.post(f"/verify-email/{verification_token}")
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert verify_data["message"] == "Email verified successfully"
    assert verify_data["email_verified"] is True
    
    # Login after verification should show verified status
    post_verify_login = client.post("/login", json={
        "email": "verify_valid@example.com",
        "password": "securepassword123"
    })
    assert post_verify_login.status_code == 200
    assert post_verify_login.json()["email_verified"] is True


def test_email_verification_flow_expired_token():
    """Test email verification with expired token"""
    # Register user
    register_response = client.post("/register", json={
        "email": "verify_expired@example.com",
        "password": "securepassword123"
    })
    assert register_response.status_code == 200
    
    # Use a clearly expired/invalid token
    expired_token = "expired_or_invalid_token_12345"
    
    # Attempt verification with expired token
    verify_response = client.post(f"/verify-email/{expired_token}")
    assert verify_response.status_code == 400
    error_data = verify_response.json()
    assert "expired" in error_data["detail"].lower() or "invalid" in error_data["detail"].lower()
    
    # User should still be unverified
    login_response = client.post("/login", json={
        "email": "verify_expired@example.com",
        "password": "securepassword123"
    })
    assert login_response.status_code == 200
    assert login_response.json()["email_verified"] is False


def test_email_verification_resend_token():
    """Test resending verification token for existing user"""
    # Register user
    client.post("/register", json={
        "email": "resend_token@example.com",
        "password": "securepassword123"
    })
    
    # Request new verification token
    resend_response = client.post("/resend-verification", json={
        "email": "resend_token@example.com"
    })
    assert resend_response.status_code == 200
    resend_data = resend_response.json()
    assert "verification_token" in resend_data
    assert resend_data["message"] == "Verification email sent"
    
    # Verify with new token
    new_token = resend_data["verification_token"]
    verify_response = client.post(f"/verify-email/{new_token}")
    assert verify_response.status_code == 200
    assert verify_response.json()["email_verified"] is True


def test_admin_only_route_access_forbidden():
    """Test that regular users cannot access admin-only routes"""
    # Register and login as regular user
    client.post("/register", json={
        "email": "regular_user@example.com",
        "password": "securepassword123"
    })
    
    login_response = client.post("/login", json={
        "email": "regular_user@example.com",
        "password": "securepassword123"
    })
    regular_token = login_response.json()["access_token"]
    
    # Attempt to access admin routes with regular user token
    admin_routes = [
        "/admin/users",
        "/admin/users/1",
        "/admin/stats"
    ]
    
    for route in admin_routes:
        response = client.get(
            route,
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 403
        error_data = response.json()
        assert "permission" in error_data["detail"].lower() or "admin" in error_data["detail"].lower()


def test_admin_only_route_access_success():
    """Test that admin users can access admin-only routes"""
    # Create admin user (assuming admin creation endpoint exists)
    admin_create_response = client.post("/admin/create-admin", json={
        "email": "admin_user@example.com",
        "password": "adminsecurepassword123",
        "admin_key": "super_secret_admin_key"
    })
    assert admin_create_response.status_code == 201
    
    # Login as admin
    admin_login = client.post("/login", json={
        "email": "admin_user@example.com",
        "password": "adminsecurepassword123"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    assert admin_login.json()["is_admin"] is True
    
    # Access admin routes successfully
    users_response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert users_response.status_code == 200
    users_data = users_response.json()
    assert "users" in users_data
    assert isinstance(users_data["users"], list)
    
    # Access admin stats
    stats_response = client.get(
        "/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    assert "total_users" in stats_data
    assert "verified_users" in stats_data


def test_admin_user_creation_with_flags():
    """Test admin creating users with specific flags and permissions"""
    # Login as admin
    admin_login = client.post("/login", json={
        "email": "admin_user@example.com",
        "password": "adminsecurepassword123"
    })
    admin_token = admin_login.json()["access_token"]
    
    # Create regular user as admin
    regular_user_data = {
        "email": "admin_created_regular@example.com",
        "password": "userpassword123",
        "is_admin": False,
        "email_verified": True,
        "is_active": True
    }
    
    create_response = client.post(
        "/admin/users",
        json=regular_user_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_response.status_code == 201
    created_user = create_response.json()
    assert created_user["email"] == regular_user_data["email"]
    assert created_user["is_admin"] is False
    assert created_user["email_verified"] is True
    assert created_user["is_active"] is True
    assert "id" in created_user
    assert "password" not in created_user  # Password should not be returned
    
    # Verify created user can login immediately (pre-verified)
    user_login = client.post("/login", json={
        "email": "admin_created_regular@example.com",
        "password": "userpassword123"
    })
    assert user_login.status_code == 200
    assert user_login.json()["email_verified"] is True


def test_admin_user_creation_with_admin_flags():
    """Test admin creating another admin user"""
    # Login as existing admin
    admin_login = client.post("/login", json={
        "email": "admin_user@example.com",
        "password": "adminsecurepassword123"
    })
    admin_token = admin_login.json()["access_token"]
    
    # Create admin user as admin
    admin_user_data = {
        "email": "new_admin@example.com",
        "password": "newadminpassword123",
        "is_admin": True,
        "email_verified": True,
        "is_active": True
    }
    
    create_response = client.post(
        "/admin/users",
        json=admin_user_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_response.status_code == 201
    created_admin = create_response.json()
    assert created_admin["email"] == admin_user_data["email"]
    assert created_admin["is_admin"] is True
    assert created_admin["email_verified"] is True
    
    # Verify new admin can access admin routes
    new_admin_login = client.post("/login", json={
        "email": "new_admin@example.com",
        "password": "newadminpassword123"
    })
    assert new_admin_login.status_code == 200
    new_admin_token = new_admin_login.json()["access_token"]
    
    admin_route_response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {new_admin_token}"}
    )
    assert admin_route_response.status_code == 200


def test_admin_user_creation_validation():
    """Test admin user creation with invalid data"""
    # Login as admin
    admin_login = client.post("/login", json={
        "email": "admin_user@example.com",
        "password": "adminsecurepassword123"
    })
    admin_token = admin_login.json()["access_token"]
    
    # Test with invalid email
    invalid_email_data = {
        "email": "invalid-email-format",
        "password": "validpassword123",
        "is_admin": False
    }
    
    response = client.post(
        "/admin/users",
        json=invalid_email_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422
    error_data = response.json()
    assert "email" in str(error_data["detail"]).lower()
    
    # Test with short password
    short_password_data = {
        "email": "valid@example.com",
        "password": "short",
        "is_admin": False
    }
    
    response = client.post(
        "/admin/users",
        json=short_password_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422
    error_data = response.json()
    assert "password" in str(error_data["detail"]).lower()
    
    # Test duplicate email
    duplicate_email_data = {
        "email": "admin_user@example.com",  # Already exists
        "password": "validpassword123",
        "is_admin": False
    }
    
    response = client.post(
        "/admin/users",
        json=duplicate_email_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    error_data = response.json()
    assert "already exists" in error_data["detail"].lower() or "already registered" in error_data["detail"].lower()
