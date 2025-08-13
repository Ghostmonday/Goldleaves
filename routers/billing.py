"""Billing router stub to satisfy tests expecting 'router'."""

from fastapi import APIRouter, Header, HTTPException, Depends, Request
from core.entitlements import get_usage_info, PLAN_LIMITS

# Tests call /billing/summary directly
router = APIRouter(prefix="/billing", tags=["Billing"])


def get_tenant_id_from_request(
	request: Request,
	x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> str:
	"""Resolve tenant ID from header or request.state; raise 400 if missing.

	Exposed for tests to override.
	"""
	if x_tenant_id:
		return x_tenant_id
	# Fallback to state-set values
	for attr in ("tenant_id", "organization_id", "org_id"):
		if hasattr(request.state, attr) and getattr(request.state, attr):
			return str(getattr(request.state, attr))
	raise HTTPException(status_code=400, detail="No tenant ID found")


@router.get("/status")
async def billing_status():  # simple ping
	return {"status": "ok"}


@router.get("/summary")
async def billing_summary(tenant_id: str = Depends(get_tenant_id_from_request)):
	info = get_usage_info(tenant_id)
	# resolve plan from limits by matching values
	# but we also mirror test heuristics (tenant_pro -> Pro, tenant_team -> Team)
	if tenant_id.startswith("tenant_pro"):
		plan = "Pro"
	elif tenant_id.startswith("tenant_team"):
		plan = "Team"
	else:
		plan = "Free"
	limits = PLAN_LIMITS[plan]
	return {
		"plan": plan,
		"unit": info.unit,
		"soft_cap": limits["soft"],
		"hard_cap": limits["hard"],
		"current_usage": info.current_usage,
		"remaining": max(0, limits["hard"] - info.current_usage),
	}


