# routers/billing.py
"""Billing router for Stripe webhook handling and billing endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import hashlib
import hmac
import json
import os

from .contract import RouterContract, RouterTags, HTTPStatus, ErrorResponseSchema, SuccessResponseSchema, register_router
from models.core_db import get_db
from models.entitlement import Entitlement, PlanType
from billing.stripe_handler import StripeWebhookHandler


class BillingRouter(RouterContract):
    """Billing router implementation."""
    
    def __init__(self):
        self._router = APIRouter()
        self._prefix = "/billing"
        self._tags = [RouterTags.BILLING]
        self.stripe_handler = StripeWebhookHandler()
        # Track processed event IDs for idempotency
        self.processed_events = set()
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
        
        @self._router.post(
            "/webhook",
            status_code=200,
            responses={
                200: {"description": "Webhook processed successfully"},
                400: {"model": ErrorResponseSchema, "description": "Invalid signature or payload"},
                409: {"description": "Event already processed (idempotent)"}
            },
            tags=self._tags,
            summary="Stripe webhook endpoint",
            description="Handle Stripe webhook events for billing updates"
        )
        async def stripe_webhook(
            request: Request,
            background_tasks: BackgroundTasks,
            db: Session = Depends(get_db)
        ):
            """Handle Stripe webhook events."""
            try:
                # Get raw payload and signature
                payload = await request.body()
                signature = request.headers.get('Stripe-Signature', '')
                
                # Verify webhook signature
                if not self.stripe_handler.verify_webhook_signature(payload, signature):
                    raise HTTPException(
                        status_code=HTTPStatus.BAD_REQUEST,
                        detail="Invalid webhook signature"
                    )
                
                # Parse event data
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=HTTPStatus.BAD_REQUEST,
                        detail="Invalid JSON payload"
                    )
                
                event_id = event.get('id')
                event_type = event.get('type')
                
                # Check for idempotency - if already processed, return 200
                if event_id in self.processed_events:
                    return JSONResponse(
                        status_code=200,
                        content={"message": "Event already processed", "event_id": event_id}
                    )
                
                # Process different event types
                result = None
                if event_type == 'checkout.session.completed':
                    result = await self.stripe_handler.handle_checkout_session_completed(event, db)
                elif event_type == 'customer.subscription.updated':
                    result = await self.stripe_handler.handle_customer_subscription_updated(event, db)
                else:
                    # Unknown event type - log and return success
                    result = {"message": f"Unhandled event type: {event_type}"}
                
                # Mark event as processed
                self.processed_events.add(event_id)
                
                # Add background task for cleanup of old processed events
                background_tasks.add_task(self._cleanup_processed_events)
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "message": "Webhook processed successfully",
                        "event_id": event_id,
                        "event_type": event_type,
                        "result": result
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                # Log error but return 200 to prevent Stripe retries for application errors
                return JSONResponse(
                    status_code=200,
                    content={
                        "message": "Webhook processing failed",
                        "error": str(e)
                    }
                )
        
        @self._router.get(
            "/summary",
            response_model=Dict[str, Any],
            tags=self._tags,
            summary="Get billing summary",
            description="Get current plan and billing information for the tenant"
        )
        async def get_billing_summary(
            request: Request,
            db: Session = Depends(get_db)
        ):
            """Get billing summary for the current tenant."""
            # In a real implementation, you'd extract tenant_id from authentication
            tenant_id = request.headers.get('X-Tenant-ID', 'default_tenant')
            
            # Get entitlement for tenant
            entitlement = db.query(Entitlement).filter(
                Entitlement.tenant_id == tenant_id
            ).first()
            
            if not entitlement:
                # Create default free entitlement
                entitlement = Entitlement(
                    tenant_id=tenant_id,
                    plan=PlanType.FREE
                )
                db.add(entitlement)
                db.commit()
                db.refresh(entitlement)
            
            # Get plan limits and current status
            plan_limits = entitlement.get_plan_limits()
            
            return {
                "tenant_id": tenant_id,
                "plan": entitlement.plan.value,
                "is_active": entitlement.is_active,
                "is_expired": entitlement.is_expired,
                "cycle_start": entitlement.cycle_start.isoformat() if entitlement.cycle_start else None,
                "cycle_end": entitlement.cycle_end.isoformat() if entitlement.cycle_end else None,
                "limits": plan_limits,
                "customer_id": entitlement.customer_id,
                "subscription_id": entitlement.subscription_id
            }
        
        @self._router.get(
            "/success",
            response_model=Dict[str, Any],
            tags=self._tags,
            summary="Billing success page",
            description="Get success confirmation after successful checkout"
        )
        async def billing_success(
            request: Request,
            session_id: str = None,
            db: Session = Depends(get_db)
        ):
            """Handle billing success page after checkout."""
            tenant_id = request.headers.get('X-Tenant-ID', 'default_tenant')
            
            # Get current entitlement
            entitlement = db.query(Entitlement).filter(
                Entitlement.tenant_id == tenant_id
            ).first()
            
            if not entitlement:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail="No billing information found"
                )
            
            plan_limits = entitlement.get_plan_limits()
            
            return {
                "success": True,
                "message": f"Successfully upgraded to {entitlement.plan.value.title()} plan!",
                "plan": {
                    "name": entitlement.plan.value.title(),
                    "limits": plan_limits,
                    "cycle_end": entitlement.cycle_end.isoformat() if entitlement.cycle_end else None
                },
                "session_id": session_id
            }
    
    def _cleanup_processed_events(self):
        """Background task to cleanup old processed event IDs."""
        # Keep only the last 1000 event IDs to prevent memory growth
        if len(self.processed_events) > 1000:
            # Convert to list, sort, and keep only recent events
            events_list = list(self.processed_events)
            # In a real implementation, you might want to persist this to database
            # For now, just keep the most recent ones
            self.processed_events = set(events_list[-500:])


# Create router instance
billing_router = BillingRouter()
router = billing_router.router