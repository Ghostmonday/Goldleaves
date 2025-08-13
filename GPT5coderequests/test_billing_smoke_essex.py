# tests/test_billing_event_smoke.py
"""Smoke test for billing events."""
import pytest
import httpx
from sqlalchemy import select
from models.billing_event import BillingEvent
from core.db.session import SessionLocal


@pytest.mark.asyncio
async def test_api_request_creates_billing_event(app, db_init):
    """
    Test that GET request to any route creates api.request billing event.
    """
    # Use httpx AsyncClient to make request
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # Make request with organization header
        response = await client.get(
            "/",
            headers={"X-Organization-ID": "123"}
        )
        
        # Assert request succeeded
        assert response.status_code == 200
    
    # Check database for billing event
    db = SessionLocal()
    try:
        # Query for billing events
        stmt = select(BillingEvent).where(
            BillingEvent.organization_id == 123,
            BillingEvent.event_name == "api.request"
        )
        result = db.execute(stmt)
        billing_events = result.scalars().all()
        
        # Assert billing event was created
        assert len(billing_events) >= 1, "No billing event found"
        
        # Check the event details
        event = billing_events[0]
        assert event.event_type == "api"
        assert event.event_name == "api.request"
        assert event.quantity == 1.0
        assert event.unit == "call"
        assert event.organization_id == 123
        
        # Check dimensions
        assert event.dimensions is not None
        assert "endpoint" in event.dimensions
        assert "method" in event.dimensions
        assert "status_code" in event.dimensions
        assert event.dimensions["endpoint"] == "/"
        assert event.dimensions["method"] == "GET"
        assert event.dimensions["status_code"] == "200"
        
    finally:
        db.close()


@pytest.mark.asyncio
async def test_health_endpoint_no_billing_event(app, db_init):
    """
    Test that /health endpoint does not create billing events.
    """
    # Clear any existing events
    db = SessionLocal()
    try:
        db.query(BillingEvent).delete()
        db.commit()
    finally:
        db.close()
    
    # Make request to health endpoint
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/health",
            headers={"X-Organization-ID": "123"}
        )
        assert response.status_code == 200
    
    # Check that no billing event was created
    db = SessionLocal()
    try:
        events = db.query(BillingEvent).filter_by(organization_id=123).all()
        assert len(events) == 0, "Health endpoint should not create billing events"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_unauthorized_no_billing_event(app, db_init):
    """
    Test that 401/403 responses do not create billing events.
    """
    # This test assumes you have an endpoint that returns 401/403
    # If not, we'll skip this test or mock it
    pass  # Placeholder - implement based on your auth setup