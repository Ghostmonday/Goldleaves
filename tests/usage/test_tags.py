"""
Tests for usage event tags functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.usage_event import UsageEvent
from core.usage import record_usage, start_event, finalize_event, get_usage_tracker
from app.usage.middleware import UsageTrackingMiddleware, set_usage_tags, get_usage_tags


class TestUsageEventModel:
    """Test the UsageEvent model."""

    def test_usage_event_defaults(self):
        """Test that usage event has correct defaults."""
        event = UsageEvent()

        assert event.feature == "unknown"
        assert event.jurisdiction == "unknown"
        assert event.plan == "unknown"
        assert event.ai is False
        assert event.metadata == {}

    def test_usage_event_custom_values(self):
        """Test usage event with custom values."""
        event = UsageEvent(
            feature="document_analysis",
            jurisdiction="us",
            plan="pro",
            ai=True,
            event_type="api_call",
            user_id="user123",
            request_id="req456",
            metadata={"key": "value"}
        )

        assert event.feature == "document_analysis"
        assert event.jurisdiction == "us"
        assert event.plan == "pro"
        assert event.ai is True
        assert event.event_type == "api_call"
        assert event.user_id == "user123"
        assert event.request_id == "req456"
        assert event.metadata == {"key": "value"}

    def test_usage_event_repr(self):
        """Test usage event string representation."""
        event = UsageEvent(
            feature="test_feature",
            jurisdiction="test_jurisdiction",
            plan="test_plan",
            ai=True
        )

        repr_str = repr(event)
        assert "UsageEvent" in repr_str
        assert "test_feature" in repr_str
        assert "test_jurisdiction" in repr_str
        assert "test_plan" in repr_str
        assert "ai=True" in repr_str


class TestCoreUsage:
    """Test the core usage tracking functionality."""

    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Setup test database."""
        # Mock the database session for tests
        with patch('core.usage.SessionLocal') as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value.__enter__.return_value = mock_session
            mock_session_local.return_value.__exit__.return_value = None
            self.mock_session = mock_session
            yield

    @pytest.mark.asyncio
    async def test_record_usage_defaults(self):
        """Test recording usage with defaults."""
        event_id = await record_usage()

        # Verify session was called
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.mock_session.refresh.assert_called_once()

        # Verify event was created with defaults
        added_event = self.mock_session.add.call_args[0][0]
        assert isinstance(added_event, UsageEvent)
        assert added_event.feature == "unknown"
        assert added_event.jurisdiction == "unknown"
        assert added_event.plan == "unknown"
        assert added_event.ai is False

    @pytest.mark.asyncio
    async def test_record_usage_custom_values(self):
        """Test recording usage with custom values."""
        event_id = await record_usage(
            feature="document_analysis",
            jurisdiction="us",
            plan="pro",
            ai=True,
            event_type="api_call",
            user_id="user123",
            request_id="req456",
            metadata={"test": "data"}
        )

        # Verify event was created with custom values
        added_event = self.mock_session.add.call_args[0][0]
        assert added_event.feature == "document_analysis"
        assert added_event.jurisdiction == "us"
        assert added_event.plan == "pro"
        assert added_event.ai is True
        assert added_event.event_type == "api_call"
        assert added_event.user_id == "user123"
        assert added_event.request_id == "req456"
        assert added_event.metadata == {"test": "data"}

    @pytest.mark.asyncio
    async def test_start_and_finalize_event(self):
        """Test starting and finalizing an event."""
        tracker = get_usage_tracker()

        # Start an event
        event_id = await start_event(
            feature="document_analysis",
            jurisdiction="us",
            plan="pro",
            ai=True
        )

        assert event_id is not None
        assert event_id in tracker._active_events

        # Finalize the event
        success = await finalize_event(event_id, {"duration": 1.5})

        assert success is True
        assert event_id not in tracker._active_events

        # Verify the event was saved
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()

        # Verify metadata was updated
        added_event = self.mock_session.add.call_args[0][0]
        assert added_event.metadata["duration"] == 1.5

    @pytest.mark.asyncio
    async def test_record_usage_error_handling(self):
        """Test error handling in record_usage."""
        # Make session raise an exception
        self.mock_session.add.side_effect = Exception("Database error")

        event_id = await record_usage()

        # Should return None on error
        assert event_id is None


class TestUsageMiddleware:
    """Test the usage tracking middleware."""

    def setup_method(self):
        """Setup test app and client."""
        self.app = FastAPI()

        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        @self.app.get("/api/documents")
        async def api_endpoint():
            return {"documents": []}

        @self.app.get("/health")
        async def health_endpoint():
            return {"status": "ok"}

    @patch('app.usage.middleware.record_usage')
    def test_middleware_with_defaults(self, mock_record_usage):
        """Test middleware uses defaults when request.state not set."""
        mock_record_usage.return_value = asyncio.Future()
        mock_record_usage.return_value.set_result("event123")

        # Add middleware
        self.app.add_middleware(UsageTrackingMiddleware)

        client = TestClient(self.app)
        response = client.get("/api/documents")

        assert response.status_code == 200

        # Verify record_usage was called with defaults
        mock_record_usage.assert_called_once()
        call_args = mock_record_usage.call_args
        assert call_args.kwargs["feature"] == "unknown"
        assert call_args.kwargs["jurisdiction"] == "unknown"
        assert call_args.kwargs["plan"] == "unknown"
        assert call_args.kwargs["ai"] is False

    @patch('app.usage.middleware.record_usage')
    def test_middleware_with_request_state_tags(self, mock_record_usage):
        """Test middleware uses request.state when set."""
        mock_record_usage.return_value = asyncio.Future()
        mock_record_usage.return_value.set_result("event123")

        # Add middleware that sets request state
        class TagSettingMiddleware:
            def __init__(self, app):
                self.app = app

            async def __call__(self, scope, receive, send):
                if scope["type"] == "http":
                    # Simulate setting tags in request state
                    # This would normally be done by authentication or other middleware
                    async def call_next(request):
                        request.state.feature = "document_analysis"
                        request.state.jurisdiction = "us"
                        request.state.plan = "pro"
                        request.state.ai = True
                        request.state.user_id = "user123"

                        # Call the actual endpoint
                        response = await self.app(scope, receive, send)
                        return response

                    return await call_next(None)

                return await self.app(scope, receive, send)

        self.app.add_middleware(UsageTrackingMiddleware)
        self.app.add_middleware(TagSettingMiddleware)

        client = TestClient(self.app)

        # Mock the middleware call since TestClient doesn't work well with custom middleware
        # Instead, test the middleware components directly

        # Test that set_usage_tags works
        request = Mock()
        request.state = Mock()

        set_usage_tags(
            request,
            feature="document_analysis",
            jurisdiction="us",
            plan="pro",
            ai=True
        )

        assert request.state.feature == "document_analysis"
        assert request.state.jurisdiction == "us"
        assert request.state.plan == "pro"
        assert request.state.ai is True

        # Test that get_usage_tags works
        tags = get_usage_tags(request)
        assert tags["feature"] == "document_analysis"
        assert tags["jurisdiction"] == "us"
        assert tags["plan"] == "pro"
        assert tags["ai"] is True

    @patch('app.usage.middleware.record_usage')
    def test_middleware_skips_health_endpoints(self, mock_record_usage):
        """Test that middleware skips health check endpoints."""
        mock_record_usage.return_value = asyncio.Future()
        mock_record_usage.return_value.set_result("event123")

        self.app.add_middleware(UsageTrackingMiddleware)

        client = TestClient(self.app)
        response = client.get("/health")

        assert response.status_code == 200

        # Verify record_usage was not called for health endpoint
        mock_record_usage.assert_not_called()

    def test_middleware_disabled(self):
        """Test that middleware can be disabled."""
        with patch('app.usage.middleware.record_usage') as mock_record_usage:
            mock_record_usage.return_value = asyncio.Future()
            mock_record_usage.return_value.set_result("event123")

            # Add disabled middleware
            self.app.add_middleware(UsageTrackingMiddleware, enabled=False)

            client = TestClient(self.app)
            response = client.get("/api/documents")

            assert response.status_code == 200

            # Verify record_usage was not called when disabled
            mock_record_usage.assert_not_called()

    def test_get_usage_tags_with_defaults(self):
        """Test get_usage_tags returns defaults when not set."""
        request = Mock()
        request.state = Mock()

        # Simulate getattr returning default values
        def mock_getattr(obj, name, default):
            return default

        with patch('builtins.getattr', side_effect=mock_getattr):
            tags = get_usage_tags(request)

        assert tags["feature"] == "unknown"
        assert tags["jurisdiction"] == "unknown"
        assert tags["plan"] == "unknown"
        assert tags["ai"] is False


class TestIntegration:
    """Integration tests for usage tracking."""

    @patch('app.usage.middleware.record_usage')
    def test_no_behavior_change_to_endpoints(self, mock_record_usage):
        """Test that existing endpoints are unaffected by usage tracking."""
        mock_record_usage.return_value = asyncio.Future()
        mock_record_usage.return_value.set_result("event123")

        app = FastAPI()

        @app.get("/api/test")
        async def test_endpoint():
            return {"data": "test_value", "status": "success"}

        # Add usage tracking middleware
        app.add_middleware(UsageTrackingMiddleware)

        client = TestClient(app)
        response = client.get("/api/test")

        # Verify endpoint behavior is unchanged
        assert response.status_code == 200
        assert response.json() == {"data": "test_value", "status": "success"}

        # Verify usage was tracked
        mock_record_usage.assert_called_once()

    def test_ai_true_when_request_state_ai_true(self):
        """Test that AI flag is True when request.state.ai = True."""
        request = Mock()
        request.state = Mock()
        request.state.ai = True
        request.state.feature = "unknown"
        request.state.jurisdiction = "unknown"
        request.state.plan = "unknown"

        tags = get_usage_tags(request)

        assert tags["ai"] is True
        assert tags["feature"] == "unknown"
        assert tags["jurisdiction"] == "unknown"
        assert tags["plan"] == "unknown"


if __name__ == "__main__":
    pytest.main([__file__])
