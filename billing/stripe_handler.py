# billing/stripe_handler.py
"""Stripe webhook handlers for checkout and subscription events."""

import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Note: stripe import will be added when dependency is available
# import stripe

from core.config import settings
from models.entitlement import PlanType


class StripeWebhookHandler:
    """Handles Stripe webhook events for billing updates."""

    def __init__(self):
        # Configure Stripe with API key (when available)
        # stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

        # Plan mapping from Stripe price IDs to app plans
        self.price_to_plan_mapping = {
            os.getenv('STRIPE_PRICE_PRO'): PlanType.PRO,
            os.getenv('STRIPE_PRICE_TEAM'): PlanType.TEAM,
        }

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature."""
        try:
            # When stripe is available:
            # stripe.Webhook.construct_event(
            #     payload, signature, self.webhook_secret
            # )
            # For now, simple validation - in production this MUST use actual Stripe verification
            return bool(signature and self.webhook_secret)
        except Exception:
            return False

    async def handle_checkout_session_completed(
        self,
        event: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Handle successful checkout completion."""
        session = event['data']['object']

        # Extract key information
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')

        # Get tenant_id from metadata or customer mapping
        tenant_id = session.get('metadata', {}).get('tenant_id')
        if not tenant_id:
            # Fallback: try to resolve tenant from customer
            tenant_id = await self._resolve_tenant_from_customer(customer_id, db)

        if not tenant_id:
            return {"error": "Could not resolve tenant for customer"}

        # Get subscription details to determine plan
        if subscription_id:
            # When stripe is available:
            # subscription = stripe.Subscription.retrieve(subscription_id)
            # For now, mock subscription data
            subscription = {"items": {"data": [{"price": {"id": os.getenv('STRIPE_PRICE_PRO')}}]}}
            plan_type = self._determine_plan_from_subscription(subscription)

            if plan_type:
                # Update or create entitlement
                await self._update_entitlement(
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    subscription_id=subscription_id,
                    plan_type=plan_type,
                    subscription=subscription,
                    db=db
                )

                return {"status": "success", "plan": plan_type.value}

        return {"error": "Could not determine plan from subscription"}

    async def handle_customer_subscription_updated(
        self,
        event: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Handle subscription updates (renewals, cancellations, plan changes)."""
        subscription = event['data']['object']

        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')

        # Resolve tenant from existing entitlement
        from models.entitlement import Entitlement
        existing_entitlement = db.query(Entitlement).filter(
            Entitlement.subscription_id == subscription_id
        ).first()

        if not existing_entitlement:
            # Try to resolve tenant from customer
            tenant_id = await self._resolve_tenant_from_customer(customer_id, db)
            if not tenant_id:
                return {"error": "Could not resolve tenant for subscription update"}
        else:
            tenant_id = existing_entitlement.tenant_id

        # Determine new plan type
        plan_type = self._determine_plan_from_subscription(subscription)

        if subscription.get('status') == 'canceled':
            # Handle cancellation - revert to free plan
            plan_type = PlanType.FREE

        # Update entitlement
        await self._update_entitlement(
            tenant_id=tenant_id,
            customer_id=customer_id,
            subscription_id=subscription_id,
            plan_type=plan_type,
            subscription=subscription,
            db=db
        )

        return {"status": "success", "plan": plan_type.value if plan_type else "free"}

    def _determine_plan_from_subscription(self, subscription: Dict[str, Any]) -> Optional[PlanType]:
        """Determine plan type from Stripe subscription."""
        items = subscription.get('items', {}).get('data', [])

        for item in items:
            price_id = item.get('price', {}).get('id')
            if price_id in self.price_to_plan_mapping:
                return self.price_to_plan_mapping[price_id]

        return None

    async def _update_entitlement(
        self,
        tenant_id: str,
        customer_id: str,
        subscription_id: str,
        plan_type: PlanType,
        subscription: Dict[str, Any],
        db: Session
    ) -> None:
        """Update or create entitlement record."""
        from models.entitlement import Entitlement

        # Parse subscription period
        current_period_start = datetime.fromtimestamp(
            subscription.get('current_period_start', 0),
            timezone.utc
        )
        current_period_end = datetime.fromtimestamp(
            subscription.get('current_period_end', 0),
            timezone.utc
        )

        # Find existing entitlement
        entitlement = db.query(Entitlement).filter(
            Entitlement.tenant_id == tenant_id
        ).first()

        if entitlement:
            # Update existing
            entitlement.customer_id = customer_id
            entitlement.subscription_id = subscription_id
            entitlement.plan = plan_type
            entitlement.cycle_start = current_period_start
            entitlement.cycle_end = current_period_end
            entitlement.updated_at = datetime.utcnow()
        else:
            # Create new
            entitlement = Entitlement(
                tenant_id=tenant_id,
                customer_id=customer_id,
                subscription_id=subscription_id,
                plan=plan_type,
                cycle_start=current_period_start,
                cycle_end=current_period_end
            )
            db.add(entitlement)

        db.commit()
        db.refresh(entitlement)

    async def _resolve_tenant_from_customer(
        self,
        customer_id: str,
        db: Session
    ) -> Optional[str]:
        """Resolve tenant ID from Stripe customer ID."""
        from models.entitlement import Entitlement

        # Try to find existing entitlement with this customer
        entitlement = db.query(Entitlement).filter(
            Entitlement.customer_id == customer_id
        ).first()

        if entitlement:
            return entitlement.tenant_id

        # If no existing entitlement found, you might need to implement
        # additional logic to map customers to tenants based on your
        # application's user/organization model
        return None
