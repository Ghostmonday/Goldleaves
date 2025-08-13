# middleware/usage.py
import time
from fastapi import Request
from services.usage_service import emit_billing_event


async def usage_logger_middleware(request: Request, call_next):
    """
    Usage logger middleware that emits billing events for API requests.
    Skips /health, /docs endpoints and 401/403 responses.
    """
    start_time = time.time()
    
    # Call downstream
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Skip certain endpoints
    path = request.url.path
    if path in ["/health", "/docs", "/openapi.json", "/redoc"]:
        return response
    
    # Skip unauthorized/forbidden responses
    if response.status_code in [401, 403]:
        return response
    
    # Emit billing event if organization_id is present
    if hasattr(request.state, "organization_id") and request.state.organization_id:
        try:
            dimensions = {
                "endpoint": path,
                "method": request.method,
                "status_code": str(response.status_code),
                "duration_ms": duration_ms
            }
            
            # Add request_id if available
            if hasattr(request.state, "request_id"):
                dimensions["request_id"] = request.state.request_id
            
            emit_billing_event(
                org_id=request.state.organization_id,
                event_type="api",
                event_name="api.request",
                quantity=1.0,
                unit="call",
                dimensions=dimensions
            )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to emit billing event: {e}")
    
    return response