"""Usage tracking middleware for request latency and result monitoring."""

import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import core.usage


class UsageMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking request latency and status codes."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track usage metrics."""
        # Record start time
        start = time.perf_counter()
        
        # Determine request_id
        request_id = self._get_request_id(request)
        
        # Initialize status_code for error handling
        status_code = 500
        
        try:
            # Process the request
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # If call_next raises, treat as 500 and re-raise to preserve behavior
            status_code = 500
            # Record the usage event before re-raising
            latency_ms = self._calculate_latency(start)
            core.usage.record_usage(request_id, status_code, latency_ms)
            raise
        
        # Calculate latency
        latency_ms = self._calculate_latency(start)
        
        # Record usage event
        core.usage.record_usage(request_id, status_code, latency_ms)
        
        return response
    
    def _get_request_id(self, request: Request) -> str:
        """Determine request ID from request state, headers, or generate new one."""
        # Check request.state.request_id first
        if hasattr(request.state, 'request_id'):
            return str(request.state.request_id)
        
        # Check X-Request-ID header
        request_id = request.headers.get("X-Request-ID")
        if request_id:
            return str(request_id)
        
        # Generate a new uuid4 string (no response header mutation)
        return str(uuid.uuid4())
    
    def _calculate_latency(self, start: float) -> int:
        """Calculate latency in milliseconds, capped to 24h."""
        latency_seconds = time.perf_counter() - start
        latency_ms = int(latency_seconds * 1000)
        
        # Cap to 24h (86_400_000 ms)
        return min(latency_ms, 86_400_000)