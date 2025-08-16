# tests/test_case.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta
from decimal import Decimal

from models.main import app
from models.user import Base, User, Organization
from models.client import Client, ClientType, ClientStatus
from models.case import Case, CaseType, CaseStatus, CasePriority, CaseBillingType
from core.db.session import get_db
from core.security import create_access_token

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_case.db"
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
def test_client_entity(db_session, test_organization):
    """Create a test client."""
    client_entity = Client(
        slug="test-client-123",
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        client_type=ClientType.INDIVIDUAL,
        status=ClientStatus.ACTIVE,
        organization_id=test_organization.id
    )
    client_entity.update_full_name()
    db_session.add(client_entity)
    db_session.commit()
    db_session.refresh(client_entity)
    return client_entity


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_case_data(test_client_entity):
    """Sample case data for testing."""
    return {
        "title": "Contract Dispute Case",
        "description": "Test case for contract dispute resolution",
        "case_type": "contract",
        "status": "open",
        "priority": "medium",
        "billing_type": "hourly",
        "hourly_rate": 350.00,
        "estimated_hours": 40.0,
        "budget": 14000.00,
        "client_id": test_client_entity.id,
        "opposing_party": "Acme Corporation",
        "tags": ["contract", "commercial", "urgent"]
    }


class TestCaseCRUD:
    """Test case CRUD operations."""

    def test_create_case(self, auth_headers, sample_case_data):
        """Test creating a new case."""
        response = client.post(
            "/api/cases/",
            json=sample_case_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Contract Dispute Case"
        assert data["case_type"] == "contract"
        assert data["status"] == "open"
        assert data["billing_type"] == "hourly"
        assert "case_number" in data
        assert len(data["tags"]) == 3
        assert data["hourly_rate"] == 350.00

    def test_create_case_invalid_client(self, auth_headers, sample_case_data):
        """Test creating case with invalid client fails."""
        sample_case_data["client_id"] = 999999  # Non-existent client

        response = client.post(
            "/api/cases/",
            json=sample_case_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_get_case_by_id(self, auth_headers, sample_case_data):
        """Test getting a case by ID."""
        # Create case
        create_response = client.post(
            "/api/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = create_response.json()["id"]

        # Get case
        response = client.get(
            f"/api/cases/{case_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == case_id
        assert data["title"] == "Contract Dispute Case"

    def test_get_case_by_number(self, auth_headers, sample_case_data):
        """Test getting a case by case number."""
        # Create case
        create_response = client.post(
            "/api/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_number = create_response.json()["case_number"]

        # Get case by number
        response = client.get(
            f"/api/cases/number/{case_number}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["case_number"] == case_number
        assert data["title"] == "Contract Dispute Case"

    def test_update_case(self, auth_headers, sample_case_data):
        """Test updating a case."""
        # Create case
        create_response = client.post(
            "/api/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = create_response.json()["id"]

        # Update case
        update_data = {
            "title": "Updated Contract Case",
            "priority": "high",
            "budget": 20000.00
        }

        response = client.put(
            f"/api/cases/{case_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Contract Case"
        assert data["priority"] == "high"
        assert data["budget"] == 20000.00

    def test_delete_case(self, auth_headers, sample_case_data):
        """Test deleting a case."""
        # Create case
        create_response = client.post(
            "/api/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = create_response.json()["id"]

        # Delete case
        response = client.delete(
            f"/api/cases/{case_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify case is deleted (soft delete)
        get_response = client.get(
            f"/api/cases/{case_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404


class TestCaseList:
    """Test case listing and filtering."""

    def test_list_cases(self, auth_headers):
        """Test listing cases with pagination."""
        response = client.get(
            "/api/cases/?skip=0&limit=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data

    def test_search_cases(self, auth_headers, sample_case_data):
        """Test searching cases."""
        # Create a case
        client.post(
            "/api/cases/",
            json=sample_case_data,
            headers=auth_headers
        )

        # Search for case
        response = client.get(
            "/api/cases/search?q=Contract",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("Contract" in c["title"] for c in data)

    def test_filter_cases_by_type(self, auth_headers, sample_case_data):
        """Test filtering cases by type."""
        # Create case
        client.post(
            "/api/cases/",
            json=sample_case_data,
            headers=auth_headers
        )

        # Filter by type
        response = client.get(
            "/api/cases/?case_type=contract",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["case_type"] == "contract"

    def test_filter_cases_by_client(self, auth_headers, sample_case_data, test_client_entity):
        """Test filtering cases by client."""
        # Create case
        client.post(
            "/api/cases/",
            json=sample_case_data,
            headers=auth_headers
        )

        # Filter by client
        response = client.get(
            f"/api/cases/?client_id={test_client_entity.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["client_id"] == test_client_entity.id

    def test_case_stats(self, auth_headers):
        """Test getting case statistics."""
        response = client.get(
            "/api/cases/stats",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_cases" in data
        assert "active_cases" in data
        assert "by_type" in data
        assert "by_status" in data


class TestCaseLifecycle:
    """Test case lifecycle operations."""

    def test_close_case(self, auth_headers, sample_case_data):
        """Test closing a case."""
        # Create case
        create_response = client.post(
            "/api/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = create_response.json()["id"]

        # Close case
        response = client.post(
            f"/api/cases/{case_id}/close?closure_reason=Case resolved successfully",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "closed"
        assert data["case_closed_date"] is not None

    def test_reopen_case(self, auth_headers, sample_case_data):
        """Test reopening a closed case."""
        # Create and close case
        create_response = client.post(
            "/api/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = create_response.json()["id"]

        client.post(
            f"/api/cases/{case_id}/close?closure_reason=Test closure",
            headers=auth_headers
        )

        # Reopen case
        response = client.post(
            f"/api/cases/{case_id}/reopen?reason=New evidence discovered",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["case_closed_date"] is None

    def test_case_deadlines(self, auth_headers):
        """Test getting upcoming case deadlines."""
        response = client.get(
            "/api/cases/deadlines?days_ahead=30",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCaseBillingTypes:
    """Test different billing types for cases."""

    def test_hourly_billing_case(self, auth_headers, sample_case_data, test_client_entity):
        """Test case with hourly billing."""
        case_data = {
            **sample_case_data,
            "billing_type": "hourly",
            "hourly_rate": 400.00
        }

        response = client.post(
            "/api/cases/",
            json=case_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["billing_type"] == "hourly"
        assert data["hourly_rate"] == 400.00

    def test_fixed_fee_case(self, auth_headers, sample_case_data):
        """Test case with fixed fee billing."""
        case_data = {
            **sample_case_data,
            "billing_type": "fixed_fee",
            "fixed_fee": 5000.00
        }

        response = client.post(
            "/api/cases/",
            json=case_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["billing_type"] == "fixed_fee"
        assert data["fixed_fee"] == 5000.00

    def test_contingency_case(self, auth_headers, sample_case_data):
        """Test case with contingency billing."""
        case_data = {
            **sample_case_data,
            "billing_type": "contingency",
            "contingency_percentage": 33.33
        }

        response = client.post(
            "/api/cases/",
            json=case_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["billing_type"] == "contingency"
        assert data["contingency_percentage"] == 33.33


class TestCaseSecurity:
    """Test case security and organization isolation."""

    def test_unauthorized_access(self, sample_case_data):
        """Test that unauthorized requests are rejected."""
        response = client.post(
            "/api/cases/",
            json=sample_case_data
        )

        assert response.status_code == 401

    def test_organization_isolation(self, db_session):
        """Test that cases are isolated by organization."""
        # This would require creating multiple organizations and users
        # and verifying that users can only access their organization's cases
        pass


class TestCaseValidation:
    """Test case data validation."""

    def test_invalid_case_type(self, auth_headers, test_client_entity):
        """Test that invalid case type is rejected."""
        invalid_data = {
            "title": "Test Case",
            "case_type": "invalid_type",
            "client_id": test_client_entity.id
        }

        response = client.post(
            "/api/cases/",
            json=invalid_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_negative_budget(self, auth_headers, sample_case_data):
        """Test that negative budget is rejected."""
        invalid_data = {
            **sample_case_data,
            "budget": -1000.00
        }

        response = client.post(
            "/api/cases/",
            json=invalid_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_invalid_hourly_rate(self, auth_headers, sample_case_data):
        """Test that invalid hourly rate is rejected."""
        invalid_data = {
            **sample_case_data,
            "billing_type": "hourly",
            "hourly_rate": -50.00
        }

        response = client.post(
            "/api/cases/",
            json=invalid_data,
            headers=auth_headers
        )

        assert response.status_code == 422
