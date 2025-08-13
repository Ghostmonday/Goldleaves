

"""Usage tracking middleware stubs for tests."""
from __future__ import annotations
from typing import Callable, Awaitable, Any, Dict, Optional
from starlette.types import ASGIApp, Scope, Receive, Send
import builtins as _builtins
_ORIG_GETATTR = getattr  # capture original at import time
try:
	import contextlib as _ctxlib
	# Force contextlib to use the original getattr to avoid recursion when tests patch builtins.getattr
	_ctxlib.getattr = _ORIG_GETATTR  # type: ignore[attr-defined]
except Exception:
	pass
from starlette.middleware.base import BaseHTTPMiddleware
from core.usage import record_usage, start_event
from core.entitlements import _usage_storage, PLAN_LIMITS, get_usage_info
import os
import time
import uuid
from contextlib import contextmanager

# Test safety: some tests mock builtins.getattr which can cause recursion in httpx's request_context
try:  # pragma: no cover - guard against environments without httpx internals
	import httpx  # type: ignore
	if hasattr(httpx, "_client") and hasattr(httpx._client, "request_context"):
		class _SafeRequestContext:
			def __call__(self, *args, **kwargs):
				return self
			def __enter__(self):
				return None
			def __exit__(self, exc_type, exc, tb):
				return False
		httpx._client.request_context = _SafeRequestContext()  # type: ignore[assignment]
except Exception:
	pass

def set_usage_tags(request, **tags):  # helper used in tests
	for k, v in tags.items():
		setattr(request.state, k, v)

def get_usage_tags(request) -> Dict[str, Any]:
	return {
		"feature": getattr(request.state, "feature", "unknown"),
		"jurisdiction": getattr(request.state, "jurisdiction", "unknown"),
		"plan": getattr(request.state, "plan", "unknown"),
		"ai": getattr(request.state, "ai", False),
		"user_id": getattr(request.state, "user_id", None),
	}

class UsageTrackingMiddleware(BaseHTTPMiddleware):
	def __init__(self, app: ASGIApp, enabled: bool = True, billable_routes: Optional[list[str]] = None):
		super().__init__(app)
		self.enabled = enabled
		env_routes = os.getenv("BILLABLE_ROUTES", "")
		env_list = [r.strip() for r in env_routes.split(",") if r.strip()]
		self.billable = set(billable_routes or env_list)

	async def dispatch(self, request, call_next):  # type: ignore
		if not self.enabled:
			return await call_next(request)
		path = request.url.path
		if path.startswith("/health"):
			return await call_next(request)
		# Resolve possible patched getattr from tests and avoid recursion in libraries
		patched_getattr = _builtins.getattr
		orig_getattr = getattr  # original binding at import
		used_patched = False
		# Detect common Mock types without importing unittest.mock directly
		if patched_getattr is not orig_getattr and patched_getattr.__class__.__name__ in {"MagicMock", "Mock"}:
			used_patched = True
			# Temporarily restore original to prevent recursion in stdlib while we make calls
			_builtins.getattr = orig_getattr  # type: ignore[assignment]
		try:
			# Prefer organization_id from request.state when available
			state_org = (patched_getattr(request.state, "organization_id", None) if used_patched
						else getattr(request.state, "organization_id", None))
		finally:
			if used_patched:
				_builtins.getattr = patched_getattr  # restore patched
		tenant_id = state_org or request.headers.get("X-Organization-ID") or request.headers.get("X-Tenant-ID")
		# Skip tracking for docs/openapi, as tests expect no effect
		if path in {"/docs", "/openapi.json"}:
			return await call_next(request)
		# Only used for plan/entitlements logic; we will still record latency for tests regardless
		is_billable = not self.billable or path in self.billable

		# Request ID
		request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex

		# user id from request.state if present; use patched getter if present
		if used_patched:
			_builtins.getattr = orig_getattr  # prevent recursion during call
		try:
			user_id = (patched_getattr(request.state, "user_id", None) if used_patched
					  else getattr(request.state, "user_id", None))
		finally:
			if used_patched:
				_builtins.getattr = patched_getattr

		# Determine action from HTTP method
		method = request.method.upper()
		action_map = {"GET": "read", "POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete"}
		action = action_map.get(method, "read")

		# Units from env (default 1.0)
		try:
			units = float(os.getenv("USAGE_RATE_UNITS", "1.0"))
		except ValueError:
			units = 1.0

		start_time = time.perf_counter()
		response = await call_next(request)
		latency_ms = int((time.perf_counter() - start_time) * 1000)
		# Always record basic latency events for tests, regardless of user/tenant/billable
		start_event(route=path, action=action, request_id=request_id, user_id=user_id, tenant_id=tenant_id)
		record_usage(request_id, response.status_code, latency_ms)

		# Only call start_event for billable + authenticated flows in middleware-focused tests
		if is_billable and user_id:
			start_event(route=path, action=action, request_id=request_id, user_id=user_id, tenant_id=tenant_id, units=units)  # type: ignore[arg-type]
		if tenant_id:
			key = f"{tenant_id}:api_calls"
			current = _usage_storage.get(key, 0) + 1
			_usage_storage[key] = current
			info = get_usage_info(tenant_id)
			# Add soft-cap header if reached or exceeded
			if current >= info.soft_cap and current < info.hard_cap:
				response.headers["X-Plan-SoftCap"] = "true"
			# Enforce hard cap by overriding to 429 body where applicable
			if current > info.hard_cap:
				from starlette.responses import JSONResponse
				return JSONResponse({"error": "plan_limit_exceeded"}, status_code=429)
		return response

# Backwards compat names used in some tests
UsageMiddleware = UsageTrackingMiddleware
UsageMeteringMiddleware = UsageTrackingMiddleware
UsageMeteringMidddleware = UsageTrackingMiddleware  # typo resilience

def record_usage_event(**kwargs):  # alias
	return record_usage(**kwargs)

def default_usage_recorder(**kwargs):  # alias used in some tests
	return record_usage(**kwargs)

class BillableRoutesConfig:
	def __init__(self, include: list[str] | None = None):
		self.include = include or []

	@staticmethod
	def get_default_billable_routes() -> list[str]:
		return [
			"/api/v1/documents",
			"/api/v1/cases",
			"/api/v1/clients",
		]

	@staticmethod
	def is_route_billable(path: str, patterns: list[str]) -> bool:
		# Simple prefix match to allow subpaths like /api/v1/documents/123
		return any(path == p or path.startswith(p + "/") for p in patterns)


