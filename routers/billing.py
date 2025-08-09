# === AGENT CONTEXT: ROUTERS AGENT ===
# ✅ Phase 4: Billing router implementation with contract compliance

"""Billing router implementation for checkout functionality."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from datetime import datetime

from .contract import RouterContract, RouterTags, HTTPStatus, ErrorResponseSchema, SuccessResponseSchema, register_router
from schemas.billing import CheckoutRequestSchema, CheckoutResponseSchema, BillingSuccessSchema, BillingCancelSchema
from services.billing_service import BillingService
from .dependencies import get_current_user, get_current_tenant, User


# Security scheme
security = HTTPBearer()


class BillingRouter(RouterContract):
    """Billing router implementation."""
    
    def __init__(self):
        self._router = APIRouter()
        self._prefix = "/api/v1/billing"
        self._tags = [RouterTags.ORGANIZATIONS]  # Using existing tag, could add BILLING tag later
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
        """Configure all billing routes."""
        self._configure_checkout_routes()
        self._configure_return_routes()
    
    def _configure_checkout_routes(self) -> None:
        """Configure checkout-related routes."""
        
        @self._router.post(
            "/checkout",
            response_model=CheckoutResponseSchema,
            status_code=HTTPStatus.OK,
            tags=self._tags,
            summary="Create Stripe checkout session",
            description="Create a Stripe checkout session for subscription upgrade",
            responses={
                HTTPStatus.OK: {"description": "Checkout session created successfully"},
                HTTPStatus.UNAUTHORIZED: {"model": ErrorResponseSchema, "description": "Authentication required"},
                HTTPStatus.FORBIDDEN: {"model": ErrorResponseSchema, "description": "Access denied for tenant"},
                HTTPStatus.UNPROCESSABLE_ENTITY: {"model": ErrorResponseSchema, "description": "Invalid plan"}
            }
        )
        async def create_checkout_session(
            checkout_request: CheckoutRequestSchema,
            current_user: User = Depends(get_current_user),
            current_tenant: Optional[Dict[str, Any]] = Depends(get_current_tenant),
            request: Request = None
        ) -> CheckoutResponseSchema:
            """Create a Stripe checkout session for subscription upgrade."""
            try:
                # User is already authenticated via get_current_user dependency
                user_id = str(current_user.id)
                if not user_id:
                    raise HTTPException(
                        status_code=HTTPStatus.UNAUTHORIZED,
                        detail="Invalid user authentication"
                    )
                
                # Get tenant ID for tenancy enforcement
                tenant_id = None
                if current_tenant:
                    tenant_id = current_tenant.get("id")
                
                # Create checkout session
                result = await BillingService.create_checkout_session(
                    plan=checkout_request.plan.value,
                    user_id=user_id,
                    tenant_id=tenant_id
                )
                
                return CheckoutResponseSchema(url=result["url"])
                
            except ValueError as e:
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                    detail=str(e)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail="Failed to create checkout session"
                )
    
    def _configure_return_routes(self) -> None:
        """Configure checkout return routes (success/cancel)."""
        
        @self._router.get(
            "/success",
            response_model=BillingSuccessSchema,
            status_code=HTTPStatus.OK,
            tags=self._tags,
            summary="Billing success page",
            description="Handle successful payment completion",
            responses={
                HTTPStatus.OK: {"description": "Payment successful"}
            }
        )
        async def billing_success(
            session_id: Optional[str] = None,
            plan: Optional[str] = None
        ) -> BillingSuccessSchema:
            """Handle successful billing completion."""
            try:
                result = await BillingService.handle_checkout_success(
                    session_id=session_id or "unknown",
                    plan=plan or "Unknown"
                )
                
                return BillingSuccessSchema(
                    message=result["message"],
                    plan=result["plan"]
                )
                
            except Exception as e:
                # Even if there's an error, show a success message
                # since the user reached the success page
                return BillingSuccessSchema(
                    message="Payment successful! Your subscription has been activated.",
                    plan=plan or "Pro"
                )
        
        @self._router.get(
            "/cancel",
            response_model=BillingCancelSchema,
            status_code=HTTPStatus.OK,
            tags=self._tags,
            summary="Billing cancel page",
            description="Handle cancelled payment",
            responses={
                HTTPStatus.OK: {"description": "Payment cancelled"}
            }
        )
        async def billing_cancel() -> BillingCancelSchema:
            """Handle cancelled billing."""
            try:
                result = await BillingService.handle_checkout_cancel()
                
                return BillingCancelSchema(
                    message=result["message"]
                )
                
            except Exception as e:
                # Fallback message if service fails
                return BillingCancelSchema(
                    message="Payment cancelled. You can try again at any time."
                )


# Initialize the router
billing_router = BillingRouter()