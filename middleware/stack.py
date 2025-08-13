"""Common middlewares: correlation, timer, tenant resolver."""
from __future__ import annotations

import os
import uuid
from typing import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response


async def correlation_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    try:
        response.headers["X-Request-ID"] = request.state.request_id
    except Exception:
        pass
    return response


async def request_timer_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    import time

    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    request.state.duration_ms = duration_ms
    try:
        response.headers["X-Response-Time-MS"] = str(duration_ms)
    except Exception:
        pass
    return response


async def tenant_resolver_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
):
    # Resolve organization_id
    org_id_header = request.headers.get("X-Organization-ID")
    if org_id_header:
        try:
            request.state.organization_id = uuid.UUID(org_id_header)
        except ValueError:
            request.state.organization_id = org_id_header
    else:
        request.state.organization_id = getattr(getattr(request, "state", object()), "organization_id", None)

    # RLS feature flag
    request.state.rls_enabled = os.getenv("RLS_ENABLED", "false").lower() == "true"

    return await call_next(request)
