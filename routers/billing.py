"""
Billing and subscription management router.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from billing.stripe import StripeService
from core.db.session import get_db
from core.dependencies import get_current_active_user, get_current_organization_id
from models.user import User

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/billing", tags=["billing"])


# Request/Response schemas
class CheckoutRequest(BaseModel):
    """Request schema for creating checkout session."""
    plan: str = Field(..., description="Subscription plan (free, pro, team)")
    success_url: str = Field(..., description="URL to redirect on successful payment")
    cancel_url: str = Field(..., description="URL to redirect on cancelled payment")
    tenant_id: Optional[int] = Field(None, description="Organization ID for team plans")


class CheckoutResponse(BaseModel):
    """Response schema for checkout session."""
    url: str = Field(..., description="Stripe checkout session URL")
    plan: str = Field(..., description="Selected plan")
    message: str = Field(..., description="Success message")


class WebhookResponse(BaseModel):
    """Response schema for webhook processing."""
    received: bool = Field(True, description="Whether webhook was received")
    processed: bool = Field(..., description="Whether webhook was processed successfully")


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Create Stripe checkout session",
    description="Create a Stripe checkout session for subscription upgrade"
)
def create_checkout_session(
    request_data: CheckoutRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> CheckoutResponse:
    """
    Create a Stripe checkout session for subscription.
    
    - **plan**: Subscription plan (free, pro, team)
    - **success_url**: URL to redirect after successful payment
    - **cancel_url**: URL to redirect after cancelled payment  
    - **tenant_id**: Organization ID (required for team plans)
    """
    try:
        # Validate tenant_id for team plans
        tenant_id = request_data.tenant_id
        if request_data.plan.lower() == "team":
            if not tenant_id:
                # Try to get from user's organization
                if user.organization_id:
                    tenant_id = user.organization_id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Organization ID required for team plans"
                    )
        
        # Create checkout session
        checkout_url = StripeService.create_checkout_session(
            user_id=user.id,
            tenant_id=tenant_id,
            plan=request_data.plan,
            success_url=request_data.success_url,
            cancel_url=request_data.cancel_url,
            db=db
        )
        
        return CheckoutResponse(
            url=checkout_url,
            plan=request_data.plan,
            message=f"Checkout session created for {request_data.plan} plan"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post(
    "/webhook",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle Stripe webhooks",
    description="Process Stripe webhook events for subscription management"
)
async def handle_webhook(
    request: Request,
    db: Session = Depends(get_db)
) -> WebhookResponse:
    """
    Handle Stripe webhook events.
    
    This endpoint processes Stripe webhooks to update subscription status
    and entitlements. It implements idempotent processing to handle webhook
    replay safely.
    """
    try:
        # Get raw body and signature
        payload = await request.body()
        signature_header = request.headers.get("stripe-signature")
        
        if not signature_header:
            logger.error("Missing Stripe signature header")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature"
            )
        
        # Verify webhook signature and get event
        event = StripeService.verify_webhook(signature_header, payload)
        
        # Process the event
        processed = StripeService.process_event(event, db)
        
        # Return success response quickly (Stripe expects 2xx within 10 seconds)
        return WebhookResponse(
            received=True,
            processed=processed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Still return 200 to acknowledge receipt
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"received": True, "processed": False, "error": str(e)}
        )


@router.get(
    "/status",
    summary="Get current subscription status",
    description="Get the current user's subscription and entitlement status"
)
def get_subscription_status(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get current user's subscription status."""
    try:
        from core.entitlements import EntitlementService
        
        # Get user's entitlement
        entitlement = EntitlementService.get_current_entitlement(
            user=user,
            tenant_id=user.organization_id,
            db=db
        )
        
        if not entitlement:
            return {
                "plan": "free",
                "active": True,
                "features": {},
                "message": "No active subscription"
            }
        
        return {
            "plan": entitlement.plan.value,
            "active": entitlement.active,
            "features": entitlement.features,
            "seats": entitlement.seats,
            "stripe_customer_id": entitlement.stripe_customer_id,
            "stripe_subscription_id": entitlement.stripe_subscription_id,
            "created_at": entitlement.created_at.isoformat() if entitlement.created_at else None,
            "updated_at": entitlement.updated_at.isoformat() if entitlement.updated_at else None
        }
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription status"
        )


# Health check endpoint for billing service
@router.get(
    "/health",
    summary="Billing service health check",
    description="Check if billing service is operational"
)
def health_check() -> dict:
    """Health check for billing service."""
    return {
        "status": "healthy",
        "service": "billing",
        "message": "Billing service is operational"
    }