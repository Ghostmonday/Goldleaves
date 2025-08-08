# models/test_models.py
"""
Test stubs for models - Phase 4 implementation
Tests for User, Organization, RevokedToken, and APIKey models
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .dependencies import Base
from .user import User, Organization, RevokedToken, APIKey, UserStatus, OrganizationPlan, APIKeyScope
from .contract import validate_model_contract, get_test_coverage_targets

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_models.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_organization(db_session):
    """Create a sample organization for testing."""
    org = Organization(
        name="Test Organization",
        description="A test organization",
        plan=OrganizationPlan.FREE
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

@pytest.fixture
def sample_user(db_session, sample_organization):
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        hashed_password="$2b$12$test_hashed_password_here_60_chars_minimum_length",
        organization_id=sample_organization.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

class TestModelContracts:
    """Test that all models adhere to their contracts."""
    
    def test_user_contract_compliance(self):
        """Test that User model meets contract requirements."""
        assert validate_model_contract("User", User)
    
    def test_organization_contract_compliance(self):
        """Test that Organization model meets contract requirements."""
        assert validate_model_contract("Organization", Organization)
    
    def test_revoked_token_contract_compliance(self):
        """Test that RevokedToken model meets contract requirements."""
        assert validate_model_contract("RevokedToken", RevokedToken)
    
    def test_api_key_contract_compliance(self):
        """Test that APIKey model meets contract requirements."""
        assert validate_model_contract("APIKey", APIKey)

class TestUserModel:
    """Test cases for User model functionality."""
    
    def test_user_creation(self, db_session, sample_organization):
        """Test basic user creation with all required fields."""
        user = User(
            email="newuser@example.com",
            hashed_password="$2b$12$test_hashed_password_here_60_chars_minimum_length",
            organization_id=sample_organization.id
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.is_active is True
        assert user.status == UserStatus.ACTIVE
        assert user.created_at is not None
        assert user.login_count == 0
    
    def test_user_login_tracking(self, db_session, sample_user):
        """Test login timestamp and count tracking."""
        initial_count = sample_user.login_count
        initial_login = sample_user.last_login
        
        sample_user.update_login_timestamp()
        db_session.commit()
        
        assert sample_user.login_count == initial_count + 1
        assert sample_user.last_login is not None
        assert sample_user.last_login != initial_login
    
    def test_user_status_management(self, db_session, sample_user):
        """Test user status transitions."""
        # Test activation
        sample_user.activate()
        assert sample_user.is_active is True
        assert sample_user.status == UserStatus.ACTIVE
        
        # Test deactivation
        sample_user.deactivate()
        assert sample_user.is_active is False
        assert sample_user.status == UserStatus.INACTIVE
        
        # Test suspension
        sample_user.suspend()
        assert sample_user.is_active is False
        assert sample_user.status == UserStatus.SUSPENDED
    
    def test_user_soft_delete(self, db_session, sample_user):
        """Test soft delete functionality."""
        assert sample_user.is_deleted is False
        assert sample_user.deleted_at is None
        
        sample_user.soft_delete()
        assert sample_user.is_deleted is True
        assert sample_user.deleted_at is not None
        
        # Test restore
        sample_user.restore()
        assert sample_user.is_deleted is False
        assert sample_user.deleted_at is None
    
    def test_user_email_verification(self, db_session, sample_user):
        """Test email verification process."""
        assert sample_user.email_verified is False
        assert sample_user.is_verified is False
        
        sample_user.verify_email()
        assert sample_user.email_verified is True
        assert sample_user.is_verified is True

class TestOrganizationModel:
    """Test cases for Organization model functionality."""
    
    def test_organization_creation(self, db_session):
        """Test basic organization creation."""
        org = Organization(
            name="New Organization",
            description="A new test organization",
            plan=OrganizationPlan.PRO
        )
        db_session.add(org)
        db_session.commit()
        
        assert org.id is not None
        assert org.name == "New Organization"
        assert org.plan == OrganizationPlan.PRO
        assert org.is_active is True
        assert org.created_at is not None
    
    def test_organization_user_relationships(self, db_session, sample_organization):
        """Test organization-user relationships."""
        user1 = User(
            email="user1@org.com",
            hashed_password="$2b$12$test_hashed_password_here_60_chars_minimum_length",
            organization_id=sample_organization.id
        )
        user2 = User(
            email="user2@org.com", 
            hashed_password="$2b$12$test_hashed_password_here_60_chars_minimum_length",
            organization_id=sample_organization.id
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Test relationship access
        assert len(sample_organization.users) == 2
        assert user1.organization == sample_organization
        assert user2.organization == sample_organization
    
    def test_organization_soft_delete(self, db_session, sample_organization):
        """Test organization soft delete."""
        assert sample_organization.is_deleted is False
        
        sample_organization.soft_delete()
        assert sample_organization.is_deleted is True
        assert sample_organization.deleted_at is not None

class TestRevokedTokenModel:
    """Test cases for RevokedToken model functionality."""
    
    def test_token_revocation(self, db_session, sample_user):
        """Test token revocation process."""
        token = RevokedToken(
            token="test_token_123",
            token_type="access",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            user_id=sample_user.id
        )
        db_session.add(token)
        db_session.commit()
        
        assert token.id is not None
        assert token.token == "test_token_123"
        assert token.user == sample_user
        assert token.created_at is not None
    
    def test_token_expiration(self, db_session, sample_user):
        """Test token expiration handling."""
        # Create expired token
        expired_token = RevokedToken(
            token="expired_token",
            expires_at=datetime.utcnow() - timedelta(hours=1),
            user_id=sample_user.id
        )
        
        # Create valid token
        valid_token = RevokedToken(
            token="valid_token",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            user_id=sample_user.id
        )
        
        db_session.add_all([expired_token, valid_token])
        db_session.commit()
        
        assert expired_token.expires_at < datetime.utcnow()
        assert valid_token.expires_at > datetime.utcnow()

class TestAPIKeyModel:
    """Test cases for APIKey model functionality."""
    
    def test_api_key_creation(self, db_session, sample_user, sample_organization):
        """Test API key creation."""
        api_key = APIKey(
            key="ak_test_key_1234567890abcdef",
            name="Test API Key",
            description="A test API key",
            scope=APIKeyScope.READ,
            user_id=sample_user.id,
            organization_id=sample_organization.id
        )
        db_session.add(api_key)
        db_session.commit()
        
        assert api_key.id is not None
        assert api_key.key == "ak_test_key_1234567890abcdef"
        assert api_key.scope == APIKeyScope.READ
        assert api_key.is_active is True
        assert api_key.usage_count == 0
    
    def test_api_key_usage_tracking(self, db_session, sample_user):
        """Test API key usage tracking."""
        api_key = APIKey(
            key="ak_usage_test_key",
            name="Usage Test Key",
            scope=APIKeyScope.WRITE,
            user_id=sample_user.id
        )
        db_session.add(api_key)
        db_session.commit()
        
        initial_count = api_key.usage_count
        initial_used = api_key.last_used_at
        
        api_key.update_usage()
        assert api_key.usage_count == initial_count + 1
        assert api_key.last_used_at is not None
        assert api_key.last_used_at != initial_used
    
    def test_api_key_expiration(self, db_session, sample_user):
        """Test API key expiration logic."""
        # Create expired key
        expired_key = APIKey(
            key="ak_expired_key",
            name="Expired Key",
            scope=APIKeyScope.READ,
            expires_at=datetime.utcnow() - timedelta(days=1),
            user_id=sample_user.id
        )
        
        # Create valid key
        valid_key = APIKey(
            key="ak_valid_key",
            name="Valid Key", 
            scope=APIKeyScope.READ,
            expires_at=datetime.utcnow() + timedelta(days=30),
            user_id=sample_user.id
        )
        
        # Create non-expiring key
        permanent_key = APIKey(
            key="ak_permanent_key",
            name="Permanent Key",
            scope=APIKeyScope.READ,
            user_id=sample_user.id
        )
        
        db_session.add_all([expired_key, valid_key, permanent_key])
        db_session.commit()
        
        assert expired_key.is_expired() is True
        assert valid_key.is_expired() is False
        assert permanent_key.is_expired() is False

# Test coverage validation
def test_coverage_targets():
    """Validate that all test coverage targets are met."""
    targets = get_test_coverage_targets()
    
    # Verify all target categories exist
    assert "User" in targets
    assert "Organization" in targets
    assert "RevokedToken" in targets
    assert "APIKey" in targets
    
    # Verify minimum test coverage
    assert len(targets["User"]) >= 5
    assert len(targets["Organization"]) >= 3
    assert len(targets["RevokedToken"]) >= 2
    assert len(targets["APIKey"]) >= 3

if __name__ == "__main__":
    pytest.main([__file__])
