"""
Billing router for usage reporting and metered billing integration.
Provides endpoints for reporting usage to external billing systems like Stripe.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.usage import get_tenant_usage_summary, generate_usage_report
from core.database import SessionLocal


# Pydantic models for request/response
class UsageReportRequest(BaseModel):
    """Request model for usage reporting."""
    tenant_id: str = Field(..., description="Tenant identifier")
    start_date: datetime = Field(..., description="Start date (UTC)")
    end_date: datetime = Field(..., description="End date (UTC)")


class UsageReportResponse(BaseModel):
    """Response model for usage reporting."""
    tenant_id: str
    period_start: str
    period_end: str
    total_events: int
    total_units: float
    total_cost_cents: int
    unique_routes: int
    route_breakdown: list[Dict[str, Any]]
    current_rate_cents: int


class StripeUsageReportRequest(BaseModel):
    """Request model for Stripe usage reporting."""
    tenant_id: str = Field(..., description="Tenant identifier")
    subscription_item_id: str = Field(..., description="Stripe subscription item ID")
    timestamp: Optional[datetime] = Field(None, description="Usage timestamp (defaults to now)")
    quantity: Optional[int] = Field(None, description="Usage quantity (defaults to current period)")


class StripeUsageReportResponse(BaseModel):
    """Response model for Stripe usage reporting."""
    success: bool
    message: str
    stripe_usage_record_id: Optional[str] = None
    reported_quantity: int
    timestamp: str


# Router instance
router = APIRouter(prefix="/billing", tags=["billing"])


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/report-usage",
    response_model=Dict[str, Any],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Report usage to external billing system",
    description="Submit usage data to external billing system (e.g., Stripe) for metered billing"
)
async def report_usage_to_stripe(
    request: StripeUsageReportRequest,
    http_request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Report usage to Stripe for metered billing.
    
    This is a stub implementation that returns 202 Accepted.
    In production, this would integrate with Stripe's usage API.
    """
    
    # Validate tenant access (user should have access to this tenant)
    user_id = getattr(http_request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get usage data for the tenant
    timestamp = request.timestamp or datetime.utcnow()
    
    if request.quantity is None:
        # Calculate quantity from current period usage
        # Default to last 30 days if not specified
        end_date = timestamp
        start_date = end_date - timedelta(days=30)
        
        summary = get_tenant_usage_summary(
            tenant_id=request.tenant_id,
            start_date=start_date,
            end_date=end_date,
            db=db
        )
        quantity = int(summary.get('total_units', 0))
    else:
        quantity = request.quantity
    
    # Stub implementation - in production, this would call Stripe API
    # Example Stripe integration:
    # ```
    # import stripe
    # usage_record = stripe.SubscriptionItem.create_usage_record(
    #     request.subscription_item_id,
    #     quantity=quantity,
    #     timestamp=int(timestamp.timestamp()),
    #     action='set'  # or 'increment'
    # )
    # ```
    
    # For now, return success response
    response_data = {
        "success": True,
        "message": "Usage report submitted successfully (stub implementation)",
        "tenant_id": request.tenant_id,
        "subscription_item_id": request.subscription_item_id,
        "reported_quantity": quantity,
        "timestamp": timestamp.isoformat(),
        "stripe_usage_record_id": f"stub_record_{timestamp.timestamp()}",
        "note": "This is a stub implementation. In production, this would integrate with Stripe's usage API."
    }
    
    return response_data


@router.get(
    "/usage-summary/{tenant_id}",
    response_model=Dict[str, Any],
    summary="Get usage summary for tenant",
    description="Get usage summary for a specific tenant within a date range"
)
async def get_usage_summary(
    tenant_id: str,
    start_date: datetime,
    end_date: datetime,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get usage summary for a tenant."""
    
    # Validate tenant access
    user_id = getattr(request.state, 'user_id', None)
    request_tenant_id = getattr(request.state, 'organization_id', None)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Simple authorization - user can only access their own tenant's data
    # In production, implement proper RBAC
    if request_tenant_id and str(request_tenant_id) != tenant_id:
        is_admin = getattr(request.state, 'is_admin', False)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to tenant data"
            )
    
    summary = get_tenant_usage_summary(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )
    
    return summary


@router.get(
    "/usage-report/{tenant_id}",
    response_model=Dict[str, Any],
    summary="Get detailed usage report",
    description="Get comprehensive usage report with route breakdown"
)
async def get_detailed_usage_report(
    tenant_id: str,
    start_date: datetime,
    end_date: datetime,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed usage report with route breakdown."""
    
    # Validate tenant access
    user_id = getattr(request.state, 'user_id', None)
    request_tenant_id = getattr(request.state, 'organization_id', None)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Simple authorization - user can only access their own tenant's data
    if request_tenant_id and str(request_tenant_id) != tenant_id:
        is_admin = getattr(request.state, 'is_admin', False)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to tenant data"
            )
    
    report = generate_usage_report(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )
    
    return report


@router.get(
    "/health",
    summary="Billing service health check",
    description="Check if billing service is operational"
)
async def billing_health_check() -> Dict[str, str]:
    """Health check for billing service."""
    return {
        "status": "healthy",
        "service": "billing",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


# Export router
__all__ = ['router']