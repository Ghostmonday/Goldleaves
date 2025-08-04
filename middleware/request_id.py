"""
Request ID middleware for tracking requests across services.
Adds a unique request ID to each request for better tracing and debugging.
"""

import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to each request."""
    
    def __init__(self, app, header_name: str = "X-Request-ID"):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            header_name: Name of the header to use for request ID
        """
        super().__init__(app)
        self.header_name = header_name
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add request ID.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint
            
        Returns:
            Response with request ID header
        """
        # Get request ID from header or generate new one
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        
        # Add request ID to request state for access in handlers
        request.state.request_id = request_id
        
        # Process the request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers[self.header_name] = request_id
        
        return response
