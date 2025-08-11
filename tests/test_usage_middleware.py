"""Tests for usage metering middleware functionality."""

import time
import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.usage.middleware import UsageMeteringMiddleware, record_usage_event, default_usage_recorder


class TestUsageMeteringMiddleware:
    """Test the UsageMeteringMiddleware class."""
    
    def test_middleware_initialization(self):
        """Test middleware initialization with default skip paths."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        assert "/health" in middleware.skip_paths
        assert "/docs" in middleware.skip_paths
        assert "/metrics" in middleware.skip_paths
    
    def test_middleware_custom_skip_paths(self):
        """Test middleware initialization with custom skip paths."""
        app = FastAPI()
        custom_paths = ["/custom", "/admin"]
        middleware = UsageMeteringMiddleware(app, skip_paths=custom_paths)
        
        assert middleware.skip_paths == custom_paths
    
    def test_should_skip_recording(self):
        """Test the skip recording logic."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        # Create mock request
        health_request = Mock()
        health_request.url.path = "/health"
        
        api_request = Mock()
        api_request.url.path = "/api/v1/users"
        
        assert middleware._should_skip_recording(health_request) is True
        assert middleware._should_skip_recording(api_request) is False
    
    def test_extract_tenant_id_from_state(self):
        """Test tenant ID extraction from request state."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        request = Mock()
        request.state = Mock()
        request.state.tenant_id = "test_tenant"
        request.headers = {}
        
        tenant_id = middleware._extract_tenant_id(request)
        assert tenant_id == "test_tenant"
    
    def test_extract_tenant_id_from_header(self):
        """Test tenant ID extraction from header."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        request = Mock()
        request.state = Mock()
        request.state.tenant_id = None
        request.headers = {"X-Tenant-ID": "header_tenant"}
        
        tenant_id = middleware._extract_tenant_id(request)
        assert tenant_id == "header_tenant"
    
    def test_extract_tenant_id_default(self):
        """Test default tenant ID extraction."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        request = Mock()
        request.state = Mock()
        request.state.tenant_id = None
        request.headers = {}
        
        tenant_id = middleware._extract_tenant_id(request)
        assert tenant_id == "public"
    
    def test_get_client_ip_from_state(self):
        """Test client IP extraction from request state."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        request = Mock()
        request.state = Mock()
        request.state.client_ip = "192.168.1.100"
        
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.100"
    
    def test_get_client_ip_from_forwarded_header(self):
        """Test client IP extraction from X-Forwarded-For header."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        request = Mock()
        request.state = Mock()
        delattr(request.state, 'client_ip')  # No client_ip in state
        request.headers = {"x-forwarded-for": "10.0.0.1, 192.168.1.1"}
        
        ip = middleware._get_client_ip(request)
        assert ip == "10.0.0.1"
    
    def test_get_client_ip_fallback(self):
        """Test client IP fallback to client.host."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        request = Mock()
        request.state = Mock()
        delattr(request.state, 'client_ip')
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        ip = middleware._get_client_ip(request)
        assert ip == "127.0.0.1"
    
    @pytest.mark.asyncio
    async def test_record_event_with_custom_recorder(self):
        """Test event recording with custom recorder."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        # Mock request and app state
        request = Mock()
        request.app = Mock()
        request.app.state = Mock()
        
        # Create mock recorder
        mock_recorder = AsyncMock()
        request.app.state.usage_recorder = mock_recorder
        
        event = {"test": "data"}
        await middleware._record_event(request, event)
        
        mock_recorder.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_record_event_with_default_recorder(self):
        """Test event recording with default recorder."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        # Mock request with no custom recorder
        request = Mock()
        request.app = Mock()
        request.app.state = Mock()
        delattr(request.app.state, 'usage_recorder')
        
        # Should not raise exception
        event = {"test": "data"}
        await middleware._record_event(request, event)
    
    @pytest.mark.asyncio
    async def test_record_event_handles_exception(self, caplog):
        """Test that recording exceptions don't fail the request."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        # Mock request with recorder that raises exception
        request = Mock()
        request.app = Mock()
        request.app.state = Mock()
        
        mock_recorder = AsyncMock(side_effect=Exception("Recording failed"))
        request.app.state.usage_recorder = mock_recorder
        
        event = {"test": "data"}
        await middleware._record_event(request, event)
        
        # Should log error but not raise
        assert "Failed to record usage event" in caplog.text


class TestDefaultUsageRecorder:
    """Test the default usage recorder."""
    
    @pytest.mark.asyncio
    async def test_default_recorder_logs_debug(self, caplog):
        """Test that default recorder logs at debug level."""
        import logging
        caplog.set_level(logging.DEBUG)
        
        event = {"tenant_id": "test", "path": "/api/v1/test"}
        await default_usage_recorder(event)
        
        assert "Usage event:" in caplog.text
        assert "test" in caplog.text


class TestMiddlewareIntegration:
    """Test middleware integration with FastAPI."""
    
    @pytest.mark.asyncio
    async def test_middleware_dispatch_creates_event(self):
        """Test that middleware dispatch creates proper usage events."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        # Mock collected events
        collected_events = []
        
        async def mock_recorder(event):
            collected_events.append(event)
        
        # Create mock request
        request = Mock()
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.headers = {"user-agent": "test-client", "X-Tenant-ID": "test_tenant"}
        request.state = Mock()
        request.state.request_id = "test-request-123"
        request.state.user_id = "user-456"
        request.app = Mock()
        request.app.state = Mock()
        request.app.state.usage_recorder = mock_recorder
        
        # Mock call_next
        async def call_next(req):
            await asyncio.sleep(0.01)  # Simulate processing time
            response = Mock()
            response.status_code = 200
            return response
        
        # Process request
        response = await middleware.dispatch(request, call_next)
        
        # Verify event was recorded
        assert len(collected_events) == 1
        event = collected_events[0]
        
        assert event["tenant_id"] == "test_tenant"
        assert event["path"] == "/api/v1/test"
        assert event["method"] == "GET"
        assert event["status_code"] == 200
        assert event["user_agent"] == "test-client"
        assert event["request_id"] == "test-request-123"
        assert event["user_id"] == "user-456"
        assert "ts" in event
        assert "processing_time_ms" in event
        assert event["processing_time_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_middleware_skips_health_endpoints(self):
        """Test that middleware skips health check endpoints."""
        app = FastAPI()
        middleware = UsageMeteringMiddleware(app)
        
        collected_events = []
        
        async def mock_recorder(event):
            collected_events.append(event)
        
        # Create health check request
        request = Mock()
        request.url.path = "/health"
        request.method = "GET"
        request.app = Mock()
        request.app.state = Mock()
        request.app.state.usage_recorder = mock_recorder
        
        async def call_next(req):
            response = Mock()
            response.status_code = 200
            return response
        
        # Process request
        await middleware.dispatch(request, call_next)
        
        # Verify no event was recorded
        assert len(collected_events) == 0


class TestEndToEndUsageMiddleware:
    """End-to-end test of usage middleware with FastAPI."""
    
    def test_usage_middleware_with_fastapi_app(self):
        """Test usage middleware integration with a real FastAPI app."""
        # Create FastAPI app
        app = FastAPI()
        
        # Collected events for verification
        collected_events = []
        
        async def test_recorder(event):
            collected_events.append(event)
        
        # Set custom recorder
        app.state.usage_recorder = test_recorder
        
        # Add middleware
        app.add_middleware(UsageMeteringMiddleware)
        
        # Add test endpoint
        @app.get("/api/v1/ping")
        async def ping():
            return {"message": "pong"}
        
        # Create test client
        client = TestClient(app)
        
        # Make request
        response = client.get("/api/v1/ping", headers={"X-Tenant-ID": "test_tenant"})
        
        # Verify response
        assert response.status_code == 200
        assert response.json() == {"message": "pong"}
        
        # Verify usage event was recorded
        assert len(collected_events) == 1
        event = collected_events[0]
        
        assert event["tenant_id"] == "test_tenant"
        assert event["path"] == "/api/v1/ping"
        assert event["method"] == "GET"
        assert event["status_code"] == 200
        assert "ts" in event
        assert "processing_time_ms" in event
    
    def test_usage_middleware_skips_docs(self):
        """Test that middleware skips documentation endpoints."""
        app = FastAPI()
        
        collected_events = []
        
        async def test_recorder(event):
            collected_events.append(event)
        
        app.state.usage_recorder = test_recorder
        app.add_middleware(UsageMeteringMiddleware)
        
        client = TestClient(app)
        
        # Request docs endpoint
        response = client.get("/docs")
        
        # Docs should be accessible but no usage event recorded
        assert response.status_code == 200
        assert len(collected_events) == 0


if __name__ == "__main__":
    pytest.main([__file__])