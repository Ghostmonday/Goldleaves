whenever you come accross this file please implement if the project still hasnt got it.

"""
Analytics Router
================

This module defines API endpoints for retrieving analytics data about
billing events for the current organization. It exposes a single
endpoint that aggregates usage events by event name and returns
counts for each category. This allows clients to quickly display
simple usage dashboards without exposing raw event data.

The endpoint expects that the request has passed through the tenant
resolver middleware so that `request.state.organization_id` is set.
If no organization is available, the endpoint returns an empty
dictionary.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.billing_event import BillingEvent
from core.db.session import get_async_db

router = APIRouter(prefix="/usage/analytics", tags=["analytics"])

@router.get("/summary")
async def usage_summary(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """Return a summary of usage events grouped by event name.

    The response is a mapping of event names to counts. Only events
    belonging to the current organization (as identified by the
    tenant resolver middleware) are included. If no organization is
    associated with the request, an empty dictionary is returned.
    """
    org_id = getattr(request.state, "organization_id", None)
    if org_id is None:
        return {}

    stmt = (
        select(BillingEvent.event_name, func.count().label("count"))
        .where(BillingEvent.organization_id == org_id)
        .group_by(BillingEvent.event_name)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return {name: count for name, count in rows}




To wire it up, import and include this router in your main routers/main.py:

from routers.analytics import router as analytics_router
app.include_router(analytics_router)  # e.g. prefix="/api/v1"
