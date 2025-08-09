"""Billing router for plan limits and usage information."""

from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.entitlements import get_usage_info

class BillingSummaryResponse(BaseModel):
    """Response model for billing summary."""
    unit: str
    soft_cap: int
    hard_cap: int
    remaining: int
    current_usage: int
    plan: str

# Create router
router = APIRouter(prefix="/billing", tags=["billing"])

def get_tenant_id_from_request(request: Request) -> str:
    """Extract tenant ID from request."""
    # Prefer request.state.tenant_id
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id:
        return tenant_id
    
    # Fallback to X-Tenant-ID header
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id
    
    # Fallback: try to derive from user_id if available
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        # In a real implementation, you'd query the user's tenant
        # For now, use user_id as tenant_id
        return f"tenant_{user_id}"
    
    raise HTTPException(
        status_code=400,
        detail="No tenant ID found in request state or headers"
    )

@router.get(
    "/summary",
    response_model=BillingSummaryResponse,
    summary="Get billing summary",
    description="Get billing summary including plan limits and current usage"
)
async def get_billing_summary(
    request: Request,
    tenant_id: str = Depends(get_tenant_id_from_request)
) -> BillingSummaryResponse:
    """Get billing summary for the current tenant."""
    try:
        usage_info = get_usage_info(tenant_id)
        
        return BillingSummaryResponse(
            unit=usage_info.unit,
            soft_cap=usage_info.soft_cap,
            hard_cap=usage_info.hard_cap,
            remaining=usage_info.remaining,
            current_usage=usage_info.current_usage,
            plan=usage_info.plan
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get billing summary: {str(e)}"
        )