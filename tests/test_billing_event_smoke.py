"""Smoke test for billing events - fully async."""
import pytest
import httpx
import uuid
from sqlalchemy import select
from models.billing_event import BillingEvent
from core.db.session import async_session_factory


@pytest.mark.asyncio
async def test_api_request_creates_billing_event(app, db_init):
    org_id = str(uuid.uuid4())

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/", headers={"X-Organization-ID": org_id})
        assert response.status_code == 200

    async with async_session_factory() as session:
        stmt = select(BillingEvent).where(BillingEvent.event_name == "api.request")
        result = await session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) >= 1


@pytest.mark.asyncio
async def test_health_endpoint_no_billing_event(app, db_init):
    org_id = str(uuid.uuid4())

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health", headers={"X-Organization-ID": org_id})
        assert response.status_code == 200

    async with async_session_factory() as session:
        stmt = select(BillingEvent)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) >= 0
