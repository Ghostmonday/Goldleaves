"""Usage metering middleware for tracking API usage."""

import time
import logging
from datetime import datetime
from typing import Dict, Any, Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


async def default_usage_recorder(event: Dict[str, Any]) -> None:
    """Default no-op usage recorder that logs at debug level.
    
    Args:
        event: Usage event data
    """
    logger.debug(f"Usage event: {event}")


async def record_usage_event(event: Dict[str, Any]) -> None:
    """Record a usage event using the configured recorder.
    
    This function is a placeholder for the actual recording logic.
    The actual recorder should be set on app.state.usage_recorder.
    
    Args:
        event: Usage event data containing tenant_id, path, method, ts, etc.
    """
    # This is just a placeholder - the real recording happens via
    # the recorder set on app.state.usage_recorder
    pass


class UsageMeteringMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking API usage events.
    
    Records usage events for API calls including tenant ID, path, method,
    and timestamp. Uses a pluggable recorder function set on app.state.usage_recorder.
    """
    
    def __init__(self, app, skip_paths: Optional[list] = None):
        """Initialize the usage metering middleware.
        
        Args:
            app: ASGI application
            skip_paths: List of path prefixes to skip recording
        """
        super().__init__(app)
        self.skip_paths = skip_paths or [
            "/health", 
            "/docs", 
            "/redoc", 
            "/openapi.json", 
            "/metrics"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and record usage event.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
        """
        # Skip recording for specified paths
        if self._should_skip_recording(request):
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Extract tenant information
        tenant_id = self._extract_tenant_id(request)
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create usage event
        event = {
            "tenant_id": tenant_id,
            "path": request.url.path,
            "method": request.method,
            "ts": datetime.utcnow().isoformat(),
            "status_code": response.status_code,
            "processing_time_ms": round(processing_time * 1000, 2),
            "user_agent": request.headers.get("user-agent", ""),
            "ip_address": self._get_client_ip(request),
            "request_id": getattr(request.state, "request_id", None)
        }
        
        # Add user information if available
        if hasattr(request.state, "user_id") and request.state.user_id:
            event["user_id"] = request.state.user_id
        
        # Record the event
        await self._record_event(request, event)
        
        return response
    
    def _should_skip_recording(self, request: Request) -> bool:
        """Determine if recording should be skipped for this request.
        
        Args:
            request: HTTP request
            
        Returns:
            True if recording should be skipped
        """
        path = request.url.path
        return any(path.startswith(skip_path) for skip_path in self.skip_paths)
    
    def _extract_tenant_id(self, request: Request) -> str:
        """Extract tenant ID from request.
        
        Checks in order:
        1. request.state.tenant_id
        2. X-Tenant-ID header
        3. defaults to 'public'
        
        Args:
            request: HTTP request
            
        Returns:
            Tenant ID string
        """
        # Check request state first
        if hasattr(request.state, "tenant_id") and request.state.tenant_id:
            return request.state.tenant_id
        
        # Check header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id
        
        # Default fallback
        return "public"
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request.
        
        Args:
            request: HTTP request
            
        Returns:
            Client IP address
        """
        # Check if already extracted by another middleware
        if hasattr(request.state, "client_ip"):
            return request.state.client_ip
        
        # Check forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _record_event(self, request: Request, event: Dict[str, Any]) -> None:
        """Record usage event using the configured recorder.
        
        Args:
            request: HTTP request (to access app state)
            event: Usage event data
        """
        try:
            # Get the recorder from app state
            recorder = getattr(request.app.state, "usage_recorder", default_usage_recorder)
            await recorder(event)
        except Exception as e:
            logger.error(f"Failed to record usage event: {e}")
            # Don't fail the request if recording fails