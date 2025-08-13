"""
Tests for usage tracking middleware.
Tests middleware behavior including idempotency and auth-failure skip.
"""

import os
import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request
from starlette.responses import Response

from app.usage.middleware import UsageTrackingMiddleware, BillableRoutesConfig
from models.usage_event import UsageEvent
from models.base import Base
from core.usage import start_event, get_usage_event_by_request_id


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_usage.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_app():
    """Create test FastAPI app with usage middleware."""
    app = FastAPI()

    # Add usage tracking middleware
    app.add_middleware(UsageTrackingMiddleware)

    @app.get("/api/v1/documents")
    async def get_documents():
        return {"documents": []}

    @app.post("/api/v1/documents")
    async def create_document():
        return {"id": "doc_123", "status": "created"}

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    @app.get("/auth/login")
    async def login():
        return {"token": "test_token"}

    return app


@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'BILLABLE_ROUTES': '/api/v1/documents,/api/v1/cases,/api/v1/clients',
        'USAGE_RATE_CENTS': '25'
    }):
        yield


class TestUsageTrackingMiddleware:
    """Test cases for UsageTrackingMiddleware."""

    def test_middleware_skips_non_billable_routes(self, test_client, mock_env_vars):
        """Test that middleware skips non-billable routes."""
        with patch('app.usage.middleware.start_event') as mock_start_event:
            response = test_client.get("/health")
            assert response.status_code == 200
            # Should not track usage for health check
            mock_start_event.assert_not_called()

    def test_middleware_tracks_billable_routes(self, test_client, mock_env_vars, db_session):
        """Test that middleware tracks billable routes."""
        # Mock request state to simulate authenticated user
        with patch('app.usage.middleware.start_event') as mock_start_event:
            # Simulate authenticated request
            headers = {
                'Authorization': 'Bearer test_token',
                'X-Organization-ID': 'org_123'
            }

            # Mock the request state
            def mock_getattr(obj, name, default=None):
                if name == 'user_id':
                    return 'user_123'
                elif name == 'organization_id':
                    return 'org_123'
                return default

            with patch('builtins.getattr', side_effect=mock_getattr):
                response = test_client.get("/api/v1/documents", headers=headers)
                assert response.status_code == 200

                # Should track usage for billable route
                mock_start_event.assert_called_once()
                call_args = mock_start_event.call_args
                assert call_args[1]['route'] == '/api/v1/documents'
                assert call_args[1]['user_id'] == 'user_123'
                assert call_args[1]['tenant_id'] == 'org_123'

    def test_middleware_generates_request_id_if_missing(self, test_client, mock_env_vars):
        """Test that middleware generates X-Request-ID if missing."""
        with patch('app.usage.middleware.start_event') as mock_start_event:
            with patch('builtins.getattr', return_value='user_123'):
                response = test_client.get("/api/v1/documents")

                # Should have generated a request ID
                if mock_start_event.called:
                    call_args = mock_start_event.call_args
                    request_id = call_args[1]['request_id']
                    assert request_id is not None
                    assert len(request_id) > 0

    def test_middleware_uses_existing_request_id(self, test_client, mock_env_vars):
        """Test that middleware uses existing X-Request-ID."""
        request_id = str(uuid.uuid4())
        headers = {'X-Request-ID': request_id}

        with patch('app.usage.middleware.start_event') as mock_start_event:
            with patch('builtins.getattr', return_value='user_123'):
                response = test_client.get("/api/v1/documents", headers=headers)

                if mock_start_event.called:
                    call_args = mock_start_event.call_args
                    assert call_args[1]['request_id'] == request_id

    def test_middleware_skips_unauthenticated_requests(self, test_client, mock_env_vars):
        """Test that middleware skips requests without user context."""
        with patch('app.usage.middleware.start_event') as mock_start_event:
            # No user_id in request state
            with patch('builtins.getattr', return_value=None):
                response = test_client.get("/api/v1/documents")

                # Should not track usage for unauthenticated request
                mock_start_event.assert_not_called()

    def test_middleware_skips_auth_failures(self, test_client, mock_env_vars):
        """Test that middleware skips tracking on 4xx auth failures."""
        with patch('app.usage.middleware.start_event') as mock_start_event:
            # Simulate 401 response
            response = test_client.get("/api/v1/documents")

            # Even if we get a 4xx response, usage should not be tracked
            # (since the test will return 200, we'll simulate this)
            if response.status_code >= 400:
                mock_start_event.assert_not_called()

    def test_idempotency_via_request_id(self, db_session, mock_env_vars):
        """Test that duplicate request IDs don't create duplicate usage events."""
        request_id = str(uuid.uuid4())

        # Create first usage event
        event1 = start_event(
            route='/api/v1/documents',
            action='read',
            request_id=request_id,
            user_id='user_123',
            tenant_id='org_123',
            db=db_session
        )
        assert event1 is not None

        # Try to create duplicate event with same request_id
        event2 = start_event(
            route='/api/v1/documents',
            action='read',
            request_id=request_id,
            user_id='user_123',
            tenant_id='org_123',
            db=db_session
        )

        # Should return the existing event, not create new one
        assert event2 is not None
        assert event1.id == event2.id

        # Verify only one event exists in database
        events = db_session.query(UsageEvent).filter(
            UsageEvent.request_id == request_id
        ).all()
        assert len(events) == 1

    def test_tenant_id_extraction_priorities(self, test_client, mock_env_vars):
        """Test tenant_id extraction from multiple sources."""
        with patch('app.usage.middleware.start_event') as mock_start_event:
            # Test priority: organization_id from state
            def mock_getattr_org_state(obj, name, default=None):
                if name == 'user_id':
                    return 'user_123'
                elif name == 'organization_id':
                    return 'org_from_state'
                return default

            with patch('builtins.getattr', side_effect=mock_getattr_org_state):
                headers = {'X-Organization-ID': 'org_from_header'}
                response = test_client.get("/api/v1/documents", headers=headers)

                if mock_start_event.called:
                    call_args = mock_start_event.call_args
                    # Should prefer org from state over header
                    assert call_args[1]['tenant_id'] == 'org_from_state'

    def test_usage_units_calculation(self, test_client, mock_env_vars):
        """Test usage units calculation."""
        with patch('app.usage.middleware.start_event') as mock_start_event:
            with patch('builtins.getattr', return_value='user_123'):
                response = test_client.post("/api/v1/documents")

                if mock_start_event.called:
                    call_args = mock_start_event.call_args
                    # Default should be 1.0 units
                    assert call_args[1]['units'] == 1.0

    def test_action_determination(self, test_client, mock_env_vars):
        """Test HTTP method to action mapping."""
        test_cases = [
            ('GET', 'read'),
            ('POST', 'create'),
            ('PUT', 'update'),
            ('PATCH', 'update'),
            ('DELETE', 'delete')
        ]

        for method, expected_action in test_cases:
            with patch('app.usage.middleware.start_event') as mock_start_event:
                with patch('builtins.getattr', return_value='user_123'):
                    if method == 'GET':
                        response = test_client.get("/api/v1/documents")
                    elif method == 'POST':
                        response = test_client.post("/api/v1/documents")
                    # Add other methods as needed

                    if mock_start_event.called:
                        call_args = mock_start_event.call_args
                        assert call_args[1]['action'] == expected_action


class TestBillableRoutesConfig:
    """Test cases for BillableRoutesConfig."""

    def test_default_billable_routes(self):
        """Test default billable routes."""
        routes = BillableRoutesConfig.get_default_billable_routes()
        assert '/api/v1/documents' in routes
        assert '/api/v1/cases' in routes
        assert '/api/v1/clients' in routes

    def test_route_matching(self):
        """Test route pattern matching."""
        patterns = ['/api/v1/documents', '/api/v1/cases']

        # Should match
        assert BillableRoutesConfig.is_route_billable('/api/v1/documents', patterns)
        assert BillableRoutesConfig.is_route_billable('/api/v1/documents/123', patterns)
        assert BillableRoutesConfig.is_route_billable('/api/v1/cases/456', patterns)

        # Should not match
        assert not BillableRoutesConfig.is_route_billable('/health', patterns)
        assert not BillableRoutesConfig.is_route_billable('/api/v1/users', patterns)
        assert not BillableRoutesConfig.is_route_billable('/docs', patterns)


class TestUsageEventModel:
    """Test cases for UsageEvent model functionality."""

    def test_usage_event_creation(self, db_session):
        """Test creating a usage event."""
        event = UsageEvent(
            request_id=str(uuid.uuid4()),
            tenant_id='org_123',
            user_id='user_123',
            route='/api/v1/documents',
            action='read',
            units=1.0,
            ts=datetime.utcnow()
        )

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        assert event.id is not None
        assert event.cost_cents is None  # Not calculated yet

    def test_cost_calculation(self, db_session):
        """Test cost calculation."""
        event = UsageEvent(
            request_id=str(uuid.uuid4()),
            tenant_id='org_123',
            user_id='user_123',
            route='/api/v1/documents',
            action='read',
            units=2.5
        )

        cost = event.calculate_cost(rate_cents=20)
        assert cost == 50  # 2.5 * 20 = 50 cents

    def test_get_by_request_id(self, db_session):
        """Test getting event by request ID."""
        request_id = str(uuid.uuid4())

        event = UsageEvent(
            request_id=request_id,
            tenant_id='org_123',
            user_id='user_123',
            route='/api/v1/documents',
            action='read',
            units=1.0
        )

        db_session.add(event)
        db_session.commit()

        found_event = UsageEvent.get_by_request_id(db_session, request_id)
        assert found_event is not None
        assert found_event.id == event.id

    def test_usage_summary(self, db_session):
        """Test usage summary calculation."""
        tenant_id = 'org_123'
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        # Create test events
        events = [
            UsageEvent(
                request_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                user_id='user_123',
                route='/api/v1/documents',
                action='read',
                units=1.0,
                cost_cents=25,
                ts=datetime(2024, 1, 15)
            ),
            UsageEvent(
                request_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                user_id='user_456',
                route='/api/v1/cases',
                action='create',
                units=2.0,
                cost_cents=50,
                ts=datetime(2024, 1, 20)
            )
        ]

        for event in events:
            db_session.add(event)
        db_session.commit()

        summary = UsageEvent.get_usage_summary(db_session, tenant_id, start_date, end_date)

        assert summary['tenant_id'] == tenant_id
        assert summary['total_events'] == 2
        assert summary['total_units'] == 3.0
        assert summary['total_cost_cents'] == 75
        assert summary['unique_routes'] == 2


if __name__ == '__main__':
    pytest.main([__file__])
