# tests/test_billing_event_smoke.py
"""Smoke test for billing events - fully async."""
import pytest
import httpx
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.billing_event import BillingEvent
from core.db.session import async_session_factory


@pytest.mark.asyncio
async def test_api_request_creates_billing_event(app, db_init):
    """
    Test that GET request to any route creates api.request billing event.
    """
    org_id = str(uuid.uuid4())
    
    # Use httpx AsyncClient to make request
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # Make request with organization header
        response = await client.get(
            "/",
            headers={"X-Organization-ID": org_id}
        )
        
        # Assert request succeeded
        assert response.status_code == 200
    
    # Check database for billing event using async session
    async with async_session_factory() as session:
        # Query for billing events
        stmt = select(BillingEvent).where(
            BillingEvent.organization_id == uuid.UUID(org_id),
            BillingEvent.event_name == "api.request"
        )
        result = await session.execute(stmt)
        billing_events = result.scalars().all()
        
        # Assert billing event was created
        assert len(billing_events) >= 1, "No billing event found"
        
        # Check the event details
        event = billing_events[0]
        assert event.event_type == "api"
        assert event.event_name == "api.request"
        assert event.quantity == 1.0
        assert event.unit == "call"
        assert event.organization_id == uuid.UUID(org_id)
        
        # Check dimensions
        assert event.dimensions is not None
        assert "endpoint" in event.dimensions
        assert "method" in event.dimensions
        assert "status_code" in event.dimensions
        assert event.dimensions["endpoint"] == "/"
        assert event.dimensions["method"] == "GET"
        assert event.dimensions["status_code"] == "200"


@pytest.mark.asyncio
async def test_health_endpoint_no_billing_event(app, db_init):
    """
    Test that /health endpoint does not create billing events.
    """
    org_id = str(uuid.uuid4())
    
    # Clear any existing events
    async with async_session_factory() as session:
        stmt = select(BillingEvent).where(
            BillingEvent.organization_id == uuid.UUID(org_id)
        )
        result = await session.execute(stmt)
        initial_count = len(result.scalars().all())
    
    # Make request to health endpoint
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/health",
            headers={"X-Organization-ID": org_id}
        )
        assert response.status_code == 200
    
    # Check that no billing event was created
    async with async_session_factory() as session:
        stmt = select(BillingEvent).where(
            BillingEvent.organization_id == uuid.UUID(org_id)
        )
        result = await session.execute(stmt)
        final_count = len(result.scalars().all())
        
        assert final_count == initial_count, "Health endpoint should not create billing events"


@pytest.mark.asyncio
async def test_request_without_org_no_billing_event(app, db_init):
    """
    Test that requests without organization_id do not create billing events.
    """
    # Count initial events
    async with async_session_factory() as session:
        stmt = select(BillingEvent)
        result = await session.execute(stmt)
        initial_count = len(result.scalars().all())
    
    # Make request without organization header
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
    
    # Verify no new billing events
    async with async_session_factory() as session:
        stmt = select(BillingEvent)
        result = await session.execute(stmt)
        final_count = len(result.scalars().all())
        
        assert final_count == initial_count, "Request without org_id should not create billing events"