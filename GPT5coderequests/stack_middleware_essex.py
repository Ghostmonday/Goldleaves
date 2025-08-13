# middleware/stack.py
import os
from fastapi import Request


async def tenant_resolver_middleware(request: Request, call_next):
    """
    Tenant resolver middleware that sets organization context.
    Sets request.state.organization_id from X-Organization-ID header or request.state.user.
    Sets request.state.rls_enabled from env RLS_ENABLED.
    """
    # Set organization_id from header or user state
    org_id = request.headers.get("X-Organization-ID")
    if org_id:
        request.state.organization_id = int(org_id)
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
    response = await call_next(request)
    return response