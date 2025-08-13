"""
Tests for Stripe billing integration.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from billing.stripe import StripeService
from models.entitlement import Entitlement, PlanType
from models.user import User, Organization


class TestStripeService:
    """Test Stripe service functionality."""

    @patch('billing.stripe.stripe.checkout.Session.create')
    @patch('billing.stripe.stripe.Customer.create')
    def test_create_checkout_session_pro_plan(
        self, mock_customer_create, mock_session_create, db_session: Session
    ):
        """Test creating checkout session for Pro plan."""
        # Setup mocks
        mock_customer_create.return_value = Mock(id="cus_test123")
        mock_session_create.return_value = Mock(
            url="https://checkout.stripe.com/test-session",
            id="cs_test_session"
        )

        # Create test user
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Test checkout session creation
        result_url = StripeService.create_checkout_session(
            user_id=1,
            tenant_id=None,
            plan="pro",
            success_url="https://app.example.com/success",
            cancel_url="https://app.example.com/cancel",
            db=db_session
        )

        # Assertions
        assert result_url == "https://checkout.stripe.com/test-session"
        mock_customer_create.assert_called_once_with(
            email="test@example.com",
            metadata={'user_id': '1'}
        )
        mock_session_create.assert_called_once()

        # Check session creation args
        call_args = mock_session_create.call_args
        assert call_args[1]['mode'] == 'subscription'
        assert call_args[1]['customer'] == "cus_test123"
        assert 'metadata' in call_args[1]
        assert call_args[1]['metadata']['user_id'] == '1'
        assert call_args[1]['metadata']['plan'] == 'pro'

    def test_create_checkout_session_free_plan(self, db_session: Session):
        """Test creating checkout session for Free plan (should skip Stripe)."""
        # Create test user
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Test free plan
        result_url = StripeService.create_checkout_session(
            user_id=1,
            tenant_id=None,
            plan="free",
            success_url="https://app.example.com/success",
            cancel_url="https://app.example.com/cancel",
            db=db_session
        )

        # Should return success URL directly for free plans
        assert result_url == "https://app.example.com/success"

        # Check that entitlement was created
        entitlement = db_session.query(Entitlement).filter(
            Entitlement.user_id == 1
        ).first()
        assert entitlement is not None
        assert entitlement.plan == PlanType.FREE
        assert entitlement.active is True

    @patch('billing.stripe.stripe.Webhook.construct_event')
    def test_verify_webhook_valid_signature(self, mock_construct_event):
        """Test webhook signature verification with valid signature."""
        # Setup mock
        test_event = {"id": "evt_test", "type": "checkout.session.completed"}
        mock_construct_event.return_value = test_event

        # Test verification
        with patch('core.config.settings.stripe_webhook_secret') as mock_secret:
            mock_secret.get_secret_value.return_value = "whsec_test"

            result = StripeService.verify_webhook(
                signature_header="t=1234567890,v1=signature",
                payload=b'{"test": "data"}'
            )

        assert result == test_event
        mock_construct_event.assert_called_once_with(
            b'{"test": "data"}',
            "t=1234567890,v1=signature",
            "whsec_test"
        )

    def test_process_event_checkout_completed(self, db_session: Session):
        """Test processing checkout.session.completed event."""
        # Create test user
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Create test event
        event = {
            "id": "evt_test123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test",
                    "customer": "cus_test123",
                    "subscription": "sub_test123",
                    "metadata": {
                        "user_id": "1",
                        "tenant_id": "",
                        "plan": "pro"
                    }
                }
            }
        }

        # Process event
        result = StripeService.process_event(event, db_session)

        # Assertions
        assert result is True

        # Check that entitlement was created/updated
        entitlement = db_session.query(Entitlement).filter(
            Entitlement.user_id == 1
        ).first()
        assert entitlement is not None
        assert entitlement.plan == PlanType.PRO
        assert entitlement.stripe_customer_id == "cus_test123"
        assert entitlement.stripe_subscription_id == "sub_test123"
        assert entitlement.active is True

    def test_process_event_idempotency(self, db_session: Session):
        """Test that processing the same event twice is safe (idempotency)."""
        # Create test user and initial entitlement
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(user)

        entitlement = Entitlement(
            user_id=1,
            plan=PlanType.PRO,
            stripe_customer_id="cus_test123",
            stripe_subscription_id="sub_test123",
            features=Entitlement.get_default_features(PlanType.PRO),
            active=True
        )
        db_session.add(entitlement)
        db_session.commit()

        # Store original values
        original_updated_at = entitlement.updated_at

        # Create test event (same subscription)
        event = {
            "id": "evt_test123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test",
                    "customer": "cus_test123",
                    "subscription": "sub_test123",
                    "metadata": {
                        "user_id": "1",
                        "tenant_id": "",
                        "plan": "pro"
                    }
                }
            }
        }

        # Process event twice
        result1 = StripeService.process_event(event, db_session)
        result2 = StripeService.process_event(event, db_session)

        # Both should succeed
        assert result1 is True
        assert result2 is True

        # Should still have only one entitlement
        entitlements = db_session.query(Entitlement).filter(
            Entitlement.user_id == 1
        ).all()
        assert len(entitlements) == 1

    def test_process_event_subscription_cancelled(self, db_session: Session):
        """Test processing subscription cancellation event."""
        # Create test user and entitlement
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(user)

        entitlement = Entitlement(
            user_id=1,
            plan=PlanType.PRO,
            stripe_customer_id="cus_test123",
            stripe_subscription_id="sub_test123",
            features=Entitlement.get_default_features(PlanType.PRO),
            active=True
        )
        db_session.add(entitlement)
        db_session.commit()

        # Create cancellation event
        event = {
            "id": "evt_cancel123",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test123",
                    "status": "canceled"
                }
            }
        }

        # Process event
        result = StripeService.process_event(event, db_session)

        # Assertions
        assert result is True

        # Check that entitlement was deactivated
        db_session.refresh(entitlement)
        assert entitlement.active is False


@pytest.fixture
def db_session():
    """Create a test database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models.base import Base

    # Create in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def client():
    """Create a test client."""
    from fastapi import FastAPI
    from routers.billing import router

    app = FastAPI()
    app.include_router(router)

    return TestClient(app)
