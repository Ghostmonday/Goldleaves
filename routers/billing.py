# === AGENT CONTEXT: ROUTERS AGENT ===
# ✅ Phase 4: Billing router implementation with contract compliance

"""Billing router implementation for billing summary endpoints."""

from fastapi import APIRouter, Request
from typing import Dict, Any
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel

from .contract import RouterContract, RouterTags, register_router


class BillingSummaryResponse(BaseModel):
    """Response model for billing summary endpoint."""
    total_usage_cents: int
    current_balance_cents: int
    next_billing_date: str


class BillingRouter(RouterContract):
    """Billing router implementation."""
    
    def __init__(self):
        self._router = APIRouter()
        self._prefix = "/api/v1/billing"
        self._tags = [RouterTags.BILLING]
        self.configure_routes()
        register_router("billing", self)
    
    @property
    def router(self) -> APIRouter:
        """FastAPI router instance."""
        return self._router
    
    @property
    def prefix(self) -> str:
        """URL prefix for this router."""
        return self._prefix
    
    @property
    def tags(self) -> list:
        """OpenAPI tags for this router."""
        return self._tags
    
    def configure_routes(self) -> None:
        """Configure billing routes."""
        
        @self._router.get(
            "/summary",
            response_model=BillingSummaryResponse,
            summary="Get billing summary",
            description="Get current billing summary including usage, balance, and next billing date"
        )
        async def get_billing_summary(request: Request) -> BillingSummaryResponse:
            """
            Get billing summary for the current user/tenant.
            
            Returns mock data for now with deterministic values.
            Scope is by tenant_id/user_id from request context if present.
            """
            # TODO: In a real implementation, extract tenant_id/user_id from request context
            # For now, return mock deterministic data
            
            # Calculate next billing date (first day of next month in UTC)
            now = datetime.now(timezone.utc)
            next_month = now + relativedelta(months=1)
            next_billing_date = next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            return BillingSummaryResponse(
                total_usage_cents=15400,  # $154.00
                current_balance_cents=2599,  # $25.99
                next_billing_date=next_billing_date.isoformat()
            )


# Create the router instance to register it
billing_router = BillingRouter()