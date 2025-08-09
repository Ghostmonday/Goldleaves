"""
Stripe integration for billing and subscription management.
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.config import settings
from core.db.session import get_db
from models.entitlement import Entitlement, PlanType
from models.user import User, Organization

# Configure Stripe
stripe.api_key = settings.stripe_secret_key.get_secret_value() if settings.stripe_secret_key else ""

logger = logging.getLogger(__name__)


class StripeService:
    """Service for handling Stripe operations."""
    
    @staticmethod
    def create_checkout_session(
        user_id: int,
        tenant_id: Optional[int],
        plan: str,
        success_url: str,
        cancel_url: str,
        db: Session = None
    ) -> str:
        """
        Create a Stripe checkout session for subscription.
        
        Args:
            user_id: ID of the user creating the subscription
            tenant_id: Optional organization/tenant ID for team plans
            plan: Plan type (free, pro, team)
            success_url: URL to redirect to on successful payment
            cancel_url: URL to redirect to on cancelled payment
            db: Database session
            
        Returns:
            Checkout session URL
        """
        if not db:
            db = next(get_db())
        
        try:
            # Validate plan
            try:
                plan_type = PlanType(plan.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid plan: {plan}"
                )
            
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # For team plans, validate tenant
            if plan_type == PlanType.TEAM and not tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tenant ID required for team plans"
                )
            
            if tenant_id:
                tenant = db.query(Organization).filter(Organization.id == tenant_id).first()
                if not tenant:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Organization not found"
                    )
            
            # Skip checkout for free plans
            if plan_type == PlanType.FREE:
                # Create or update free entitlement directly
                StripeService._create_or_update_entitlement(
                    db=db,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    plan_type=plan_type,
                    stripe_customer_id=None,
                    stripe_subscription_id=None
                )
                return success_url
            
            # Create or retrieve Stripe customer
            customer_id = StripeService._get_or_create_customer(user, db)
            
            # Map plan to Stripe price ID (these would be configured in Stripe dashboard)
            price_mapping = {
                PlanType.PRO: "price_pro_monthly",  # Replace with actual Stripe Price ID
                PlanType.TEAM: "price_team_monthly",  # Replace with actual Stripe Price ID
            }
            
            price_id = price_mapping.get(plan_type)
            if not price_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No pricing configured for plan: {plan}"
                )
            
            # Create idempotency key
            idempotency_key = hashlib.sha256(
                f"{user_id}:{tenant_id}:{plan}:{datetime.utcnow().isoformat()}"
                .encode()
            ).hexdigest()[:24]
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user_id),
                    'tenant_id': str(tenant_id) if tenant_id else '',
                    'plan': plan,
                },
                idempotency_key=idempotency_key
            )
            
            logger.info(f"Created checkout session {session.id} for user {user_id}, plan {plan}")
            return session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create checkout session"
            )
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            raise
    
    @staticmethod
    def verify_webhook(signature_header: str, payload: bytes) -> Dict[str, Any]:
        """
        Verify Stripe webhook signature and return event data.
        
        Args:
            signature_header: Stripe signature header
            payload: Raw webhook payload
            
        Returns:
            Parsed webhook event
            
        Raises:
            HTTPException: If signature verification fails
        """
        webhook_secret = settings.stripe_webhook_secret.get_secret_value()
        if not webhook_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook secret not configured"
            )
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
    
    @staticmethod
    def process_event(event: Dict[str, Any], db: Session = None) -> bool:
        """
        Process Stripe webhook event idempotently.
        
        Args:
            event: Stripe webhook event
            db: Database session
            
        Returns:
            True if event was processed successfully
        """
        if not db:
            db = next(get_db())
        
        event_id = event['id']
        event_type = event['type']
        
        logger.info(f"Processing Stripe event {event_id} of type {event_type}")
        
        # Check if we've already processed this event (idempotency)
        if StripeService._is_event_processed(event_id, db):
            logger.info(f"Event {event_id} already processed, skipping")
            return True
        
        try:
            # Process different event types
            if event_type == 'checkout.session.completed':
                StripeService._handle_checkout_completed(event['data']['object'], db)
            elif event_type == 'invoice.payment_succeeded':
                StripeService._handle_payment_succeeded(event['data']['object'], db)
            elif event_type == 'invoice.payment_failed':
                StripeService._handle_payment_failed(event['data']['object'], db)
            elif event_type == 'customer.subscription.updated':
                StripeService._handle_subscription_updated(event['data']['object'], db)
            elif event_type == 'customer.subscription.deleted':
                StripeService._handle_subscription_cancelled(event['data']['object'], db)
            else:
                logger.info(f"Unhandled event type: {event_type}")
            
            # Mark event as processed
            StripeService._mark_event_processed(event_id, event_type, db)
            db.commit()
            
            logger.info(f"Successfully processed event {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing event {event_id}: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def _get_or_create_customer(user: User, db: Session) -> str:
        """Get or create Stripe customer for user."""
        # Check if user already has a customer ID in existing entitlement
        existing_entitlement = db.query(Entitlement).filter(
            Entitlement.user_id == user.id,
            Entitlement.stripe_customer_id.isnot(None)
        ).first()
        
        if existing_entitlement and existing_entitlement.stripe_customer_id:
            return existing_entitlement.stripe_customer_id
        
        # Create new customer
        customer = stripe.Customer.create(
            email=user.email,
            metadata={'user_id': str(user.id)}
        )
        
        return customer.id
    
    @staticmethod
    def _create_or_update_entitlement(
        db: Session,
        user_id: int,
        tenant_id: Optional[int],
        plan_type: PlanType,
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None
    ) -> Entitlement:
        """Create or update entitlement."""
        # Find existing entitlement
        query = db.query(Entitlement)
        if tenant_id:
            entitlement = query.filter(Entitlement.tenant_id == tenant_id).first()
        else:
            entitlement = query.filter(Entitlement.user_id == user_id).first()
        
        if entitlement:
            # Update existing
            entitlement.plan = plan_type
            entitlement.features = Entitlement.get_default_features(plan_type)
            if stripe_customer_id:
                entitlement.stripe_customer_id = stripe_customer_id
            if stripe_subscription_id:
                entitlement.stripe_subscription_id = stripe_subscription_id
            entitlement.activate()
        else:
            # Create new
            entitlement = Entitlement(
                user_id=user_id if not tenant_id else None,
                tenant_id=tenant_id,
                plan=plan_type,
                features=Entitlement.get_default_features(plan_type),
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
                active=True
            )
            db.add(entitlement)
        
        return entitlement
    
    @staticmethod
    def _handle_checkout_completed(session: Dict[str, Any], db: Session) -> None:
        """Handle successful checkout completion."""
        metadata = session.get('metadata', {})
        user_id = int(metadata.get('user_id'))
        tenant_id = int(metadata.get('tenant_id')) if metadata.get('tenant_id') else None
        plan = metadata.get('plan')
        
        if not user_id or not plan:
            logger.error(f"Missing metadata in checkout session: {session['id']}")
            return
        
        plan_type = PlanType(plan.lower())
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        
        StripeService._create_or_update_entitlement(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            plan_type=plan_type,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id
        )
        
        logger.info(f"Activated {plan} plan for user {user_id}")
    
    @staticmethod
    def _handle_payment_succeeded(invoice: Dict[str, Any], db: Session) -> None:
        """Handle successful payment."""
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            return
        
        # Find entitlement by subscription ID
        entitlement = db.query(Entitlement).filter(
            Entitlement.stripe_subscription_id == subscription_id
        ).first()
        
        if entitlement:
            entitlement.activate()
            logger.info(f"Renewed entitlement {entitlement.id} for subscription {subscription_id}")
    
    @staticmethod
    def _handle_payment_failed(invoice: Dict[str, Any], db: Session) -> None:
        """Handle failed payment."""
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            return
        
        # Find entitlement by subscription ID
        entitlement = db.query(Entitlement).filter(
            Entitlement.stripe_subscription_id == subscription_id
        ).first()
        
        if entitlement:
            # Don't immediately deactivate - Stripe will retry
            logger.warning(f"Payment failed for entitlement {entitlement.id}, subscription {subscription_id}")
    
    @staticmethod
    def _handle_subscription_updated(subscription: Dict[str, Any], db: Session) -> None:
        """Handle subscription updates."""
        subscription_id = subscription['id']
        status = subscription['status']
        
        entitlement = db.query(Entitlement).filter(
            Entitlement.stripe_subscription_id == subscription_id
        ).first()
        
        if entitlement:
            if status == 'active':
                entitlement.activate()
            elif status in ['canceled', 'unpaid', 'past_due']:
                entitlement.deactivate()
            
            logger.info(f"Updated entitlement {entitlement.id} status based on subscription {subscription_id}")
    
    @staticmethod
    def _handle_subscription_cancelled(subscription: Dict[str, Any], db: Session) -> None:
        """Handle subscription cancellation."""
        subscription_id = subscription['id']
        
        entitlement = db.query(Entitlement).filter(
            Entitlement.stripe_subscription_id == subscription_id
        ).first()
        
        if entitlement:
            entitlement.deactivate()
            logger.info(f"Deactivated entitlement {entitlement.id} for cancelled subscription {subscription_id}")
    
    @staticmethod
    def _is_event_processed(event_id: str, db: Session) -> bool:
        """Check if webhook event has already been processed."""
        # In a real implementation, you'd store processed event IDs in a table
        # For now, we'll use a simple approach with the audit system
        # This is a placeholder - implement proper event tracking
        return False
    
    @staticmethod
    def _mark_event_processed(event_id: str, event_type: str, db: Session) -> None:
        """Mark webhook event as processed."""
        # In a real implementation, you'd store this in a webhook_events table
        # For now, this is a placeholder
        logger.info(f"Marked event {event_id} ({event_type}) as processed")


# Export functions for backward compatibility
create_checkout_session = StripeService.create_checkout_session
verify_webhook = StripeService.verify_webhook
process_event = StripeService.process_event