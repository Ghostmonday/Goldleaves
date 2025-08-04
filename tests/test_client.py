# tests/test_client.py

from typing import Any
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date

from models.main import app
from models.user import Base, User, Organization
from models.client import Client, ClientType, ClientStatus, ClientPriority, Language
from core.db.session import get_db
from core.security import create_access_token

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_client.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def db_session():
    """Create a test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_organization(db_session):
    """Create a test organization."""
    org = Organization(
        name="Test Legal Firm",
        domain="testlegal.com",
        type="law_firm",
        is_active=True
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def test_user(db_session, test_organization):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@testlegal.com",
        first_name="Test",
        last_name="User",
        role="ADMIN",
        organization_id=test_organization.id,
        is_active=True,
        is_verified=True
    )
    user.set_password("testpassword123")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_client_data():
    """Sample client data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "client_type": "individual",
        "status": "active",
        "priority": "medium",
        "preferred_language": "en",
        "notes": "Test client for unit testing",
        "address": {
            "line1": "123 Main St",
            "city": "Anytown",
            "state_province": "CA",
            "postal_code": "12345",
            "country": "US"
        },
        "tags": ["test", "demo"]
    }


class TestClientCRUD:
    """Test client CRUD operations."""
    
    def test_create_client(self, auth_headers, sample_client_data):
        """Test creating a new client."""
        response = client.post(
            "/api/clients/",
            json=sample_client_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john.doe@example.com"
        assert data["client_type"] == "individual"
        assert data["status"] == "active"
        assert "slug" in data
        assert len(data["tags"]) == 2
    
    def test_create_client_duplicate_email(self, auth_headers, sample_client_data):
        """Test creating client with duplicate email fails."""
        # Create first client
        client.post(
            "/api/clients/",
            json=sample_client_data,
            headers=auth_headers
        )
        
        # Try to create second client with same email
        response = client.post(
            "/api/clients/",
            json=sample_client_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_get_client_by_id(self, auth_headers, sample_client_data):
        """Test getting a client by ID."""
        # Create client
        create_response = client.post(
            "/api/clients/",
            json=sample_client_data,
            headers=auth_headers
        )
        client_id = create_response.json()["id"]
        
        # Get client
        response = client.get(
            f"/api/clients/{client_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == client_id
        assert data["first_name"] == "John"
    
    def test_get_client_by_slug(self, auth_headers, sample_client_data):
        """Test getting a client by slug."""
        # Create client
        create_response = client.post(
            "/api/clients/",
            json=sample_client_data,
            headers=auth_headers
        )
        slug = create_response.json()["slug"]
        
        # Get client by slug
        response = client.get(
            f"/api/clients/slug/{slug}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == slug
        assert data["first_name"] == "John"
    
    def test_update_client(self, auth_headers, sample_client_data):
        """Test updating a client."""
        # Create client
        create_response = client.post(
            "/api/clients/",
            json=sample_client_data,
            headers=auth_headers
        )
        client_id = create_response.json()["id"]
        
        # Update client
        update_data = {
            "first_name": "Jane",
            "priority": "high",
            "notes": "Updated notes"
        }
        
        response = client.put(
            f"/api/clients/{client_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["priority"] == "high"
        assert data["notes"] == "Updated notes"
    
    def test_delete_client(self, auth_headers, sample_client_data):
        """Test deleting a client."""
        # Create client
        create_response = client.post(
            "/api/clients/",
            json=sample_client_data,
            headers=auth_headers
        )
        client_id = create_response.json()["id"]
        
        # Delete client
        response = client.delete(
            f"/api/clients/{client_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify client is deleted (soft delete)
        get_response = client.get(
            f"/api/clients/{client_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404


class TestClientList:
    """Test client listing and filtering."""
    
    def test_list_clients(self, auth_headers):
        """Test listing clients with pagination."""
        response = client.get(
            "/api/clients/?skip=0&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
    
    def test_search_clients(self, auth_headers, sample_client_data):
        """Test searching clients."""
        # Create a client
        client.post(
            "/api/clients/",
            json=sample_client_data,
            headers=auth_headers
        )
        
        # Search for client
        response = client.get(
            "/api/clients/search?q=John",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(c["first_name"] == "John" for c in data)
    
    def test_filter_clients_by_type(self, auth_headers, sample_client_data):
        """Test filtering clients by type."""
        # Create client
        client.post(
            "/api/clients/",
            json=sample_client_data,
            headers=auth_headers
        )
        
        # Filter by type
        response = client.get(
            "/api/clients/?client_type=individual",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["client_type"] == "individual"
    
    def test_client_stats(self, auth_headers):
        """Test getting client statistics."""
        response = client.get(
            "/api/clients/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_clients" in data
        assert "active_clients" in data
        assert "by_type" in data
        assert "by_status" in data


class TestClientBulkOperations:
    """Test client bulk operations."""
    
    def test_bulk_update_status(self, auth_headers):
        """Test bulk updating client status."""
        # Create multiple clients
        client_ids = []
        for i in range(3):
            client_data = {
                "first_name": f"Client{i}",
                "last_name": "Test",
                "email": f"client{i}@test.com",
                "client_type": "individual",
                "status": "prospect"
            }
            response = client.post(
                "/api/clients/",
                json=client_data,
                headers=auth_headers
            )
            client_ids.append(response.json()["id"])
        
        # Bulk update status
        bulk_data = {
            "client_ids": client_ids,
            "action": "update_status",
            "parameters": {"status": "active"}
        }
        
        response = client.post(
            "/api/clients/bulk",
            json=bulk_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
        assert data["error_count"] == 0
        assert len(data["updated_clients"]) == 3


class TestClientSecurity:
    """Test client security and organization isolation."""
    
    def test_unauthorized_access(self, sample_client_data):
        """Test that unauthorized requests are rejected."""
        response = client.post(
            "/api/clients/",
            json=sample_client_data
        )
        
        assert response.status_code == 401
    
    def test_organization_isolation(self, db_session):
        """Test that clients are isolated by organization."""
        # This would require creating multiple organizations and users
        # and verifying that users can only access their organization's clients
        pass


class TestClientValidation:
    """Test client data validation."""
    
    def test_invalid_email_format(self, auth_headers):
        """Test that invalid email format is rejected."""
        invalid_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "invalid-email",
            "client_type": "individual"
        }
        
        response = client.post(
            "/api/clients/",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_invalid_client_type(self, auth_headers):
        """Test that invalid client type is rejected."""
        invalid_data = {
            "first_name": "Test",
            "last_name": "User",
            "client_type": "invalid_type"
        }
        
        response = client.post(
            "/api/clients/",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
