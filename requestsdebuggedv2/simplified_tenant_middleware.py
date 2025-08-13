# middleware/stack.py
import os
import uuid
from fastapi import Request


async def correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to request."""
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


async def request_timer_middleware(request: Request, call_next):
    """Time request duration."""
    import time
    start_time = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start_time) * 1000)
    request.state.duration_ms = duration_ms
    response.headers["X-Response-Time-MS"] = str(duration_ms)
    return response


async def tenant_resolver_middleware(request: Request, call_next):
    """
    Tenant resolver middleware that sets organization context.
    Sets request.state.organization_id from X-Organization-ID header or request.state.user.
    Sets request.state.rls_enabled from env RLS_ENABLED.
    
    Note: Postgres GUCs are now set in get_async_db() dependency to ensure
    they apply to the actual session used by routes.
    """
    # Set organization_id from header or user state
    org_id = request.headers.get("X-Organization-ID")
    if org_id:
        try:
            # Convert to UUID if it's a valid UUID string
            request.state.organization_id = uuid.UUID(org_id)
        except ValueError:
            # Keep as string if not valid UUID (shouldn't happen in production)
            request.state.organization_id = org_id
    elif hasattr(request.state, "user") and request.state.user:
        # Assuming user has organization_id attribute
        if hasattr(request.state.user, "organization_id"):
            request.state.organization_id = request.state.user.organization_id
        elif isinstance(request.state.user, dict) and "organization_id" in request.state.user:
            request.state.organization_id = request.state.user["organization_id"]
    else:
        request.state.organization_id = None
    
    # Set RLS enabled flag from environment
    rls_enabled = os.getenv("RLS_ENABLED", "false").lower() == "true"
    request.state.rls_enabled = rls_enabled
    
    # Continue processing
    # Note: GUCs are now set in get_async_db() to ensure correct session scope
    response = await call_next(request)
    return response