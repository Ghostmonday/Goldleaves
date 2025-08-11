# === AGENT CONTEXT: ROUTERS AGENT ===
# ✅ Usage router for live metering endpoints

"""Usage router providing live metering data endpoints."""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .contract import RouterTags, HTTPStatus
from .dependencies import get_current_user, get_tenant_context

router = APIRouter()

# Request/Response schemas
class UsageSummaryResponse(BaseModel):
    """Usage summary response schema."""
    total_calls: int = Field(description="Total number of API calls in the current window")
    est_cost_cents: int = Field(description="Estimated cost in cents")
    window_start: datetime = Field(description="Start of the usage window (UTC)")
    window_end: datetime = Field(description="End of the usage window (UTC)")

class DailyUsageItem(BaseModel):
    """Daily usage item schema."""
    date: str = Field(description="Date in YYYY-MM-DD format")
    calls: int = Field(description="Number of calls on this date")

class DailyUsageResponse(BaseModel):
    """Daily usage response schema."""
    usage: List[DailyUsageItem] = Field(description="Daily usage data")

@router.get(
    "/api/v1/usage/summary",
    response_model=UsageSummaryResponse,
    tags=[RouterTags.USAGE],
    summary="Get usage summary",
    description="Get total API calls and estimated cost for the current billing window"
)
async def get_usage_summary(
    user_context: Dict[str, Any] = Depends(get_current_user),
    tenant_context: Dict[str, Any] = Depends(get_tenant_context)
) -> UsageSummaryResponse:
    """Get usage summary for the current user/tenant."""
    try:
        # Mock implementation - in production this would query actual metering data
        # Scoped by tenant_id/user_id from context
        tenant_id = tenant_context.get("tenant_id")
        user_id = user_context.get("user_id")
        
        # Calculate current billing window (e.g., monthly)
        now = datetime.utcnow()
        window_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Mock data - in production this would be from a metering service
        total_calls = 1250
        rate_cents_per_call = 2  # 2 cents per call
        est_cost_cents = total_calls * rate_cents_per_call
        
        return UsageSummaryResponse(
            total_calls=total_calls,
            est_cost_cents=est_cost_cents,
            window_start=window_start,
            window_end=now
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage summary: {str(e)}"
        )

@router.get(
    "/api/v1/usage/daily",
    response_model=DailyUsageResponse,
    tags=[RouterTags.USAGE],
    summary="Get daily usage",
    description="Get daily API call counts for a specified number of days"
)
async def get_daily_usage(
    days: int = 7,
    user_context: Dict[str, Any] = Depends(get_current_user),
    tenant_context: Dict[str, Any] = Depends(get_tenant_context)
) -> DailyUsageResponse:
    """Get daily usage data for the specified number of days."""
    try:
        # Validate days parameter
        if days < 1 or days > 90:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Days parameter must be between 1 and 90"
            )
        
        # Scoped by tenant_id/user_id from context
        tenant_id = tenant_context.get("tenant_id")
        user_id = user_context.get("user_id")
        
        # Generate mock daily data - in production this would be from a metering service
        now = datetime.utcnow()
        usage_data = []
        
        for i in range(days):
            date = now - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            # Mock varying call counts
            calls = max(0, 100 + (i * 15) - (i * i // 2))
            usage_data.append(DailyUsageItem(date=date_str, calls=calls))
        
        # Reverse to get chronological order (oldest first)
        usage_data.reverse()
        
        return DailyUsageResponse(usage=usage_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve daily usage: {str(e)}"
        )