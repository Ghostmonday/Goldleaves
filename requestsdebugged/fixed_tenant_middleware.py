# middleware/stack.py
import os
import uuid
from fastapi import Request
from sqlalchemy import text
from core.db.session import async_session_factory


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
    Tenant resolver middleware that sets organization context and Postgres GUCs.
    Sets request.state.organization_id from X-Organization-ID header or request.state.user.
    Sets request.state.rls_enabled from env RLS_ENABLED.
    Configures Postgres session variables for RLS.
    """
    # Set organization_id from header or user state
    org_id = request.headers.get("X-Organization-ID")
    if org_id:
        try:
            # Convert to UUID if it's a valid UUID string
            request.state.organization_id = uuid.UUID(org_id)
        except ValueError:
            request.state.organization_id = org_id  # Keep as string if not valid UUID
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
    
    # Set Postgres GUCs if we have an org_id and RLS is enabled
    if request.state.organization_id and rls_enabled:
        async with async_session_factory() as session:
            try:
                # Set session-level config for RLS
                await session.execute(
                    text("SET LOCAL app.current_org = :org_id"),
                    {"org_id": str(request.state.organization_id)}
                )
                await session.execute(
                    text("SET LOCAL app.rls_enabled = :enabled"),
                    {"enabled": "true" if rls_enabled else "false"}
                )
                await session.commit()
            except Exception as e:
                # Log error but don't fail the request
                print(f"Failed to set Postgres GUCs: {e}")
                await session.rollback()
    
    # Continue processing
    response = await call_next(request)
    return response