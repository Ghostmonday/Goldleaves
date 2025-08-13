"""Usage logger middleware (emits billing events after response)."""
from __future__ import annotations

import time
from typing import Any, Awaitable, Callable, Dict
from uuid import UUID

from starlette.requests import Request
from starlette.responses import Response

from services.usage_service import emit_billing_event


async def usage_logger_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
):
    start = time.time()
    response = await call_next(request)

    path = request.url.path
    if path in ("/health", "/docs", "/openapi.json", "/redoc"):
        return response
    if response.status_code in (401, 403):
        return response

    org_id = getattr(request.state, "organization_id", None)
    if not org_id:
        return response

    # Normalize org_id to UUID if string
    if isinstance(org_id, str):
        try:
            org_id = UUID(org_id)
        except ValueError:
            return response

    dims: Dict[str, Any] = {
        "endpoint": path,
        "method": request.method,
        "status_code": str(response.status_code),
        "duration_ms": int((time.time() - start) * 1000),
    }
    rid = getattr(request.state, "request_id", None)
    if rid:
        dims["request_id"] = str(rid)

    try:
        await emit_billing_event(
            org_id=org_id,
            event_type="api",
            event_name="api.request",
            quantity=1.0,
            unit="call",
            dimensions=dims,
        )
    except Exception:
        # Non-fatal in tests
        pass

    return response
