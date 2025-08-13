"""Async usage service to emit billing events."""
from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from core.db.session import async_session_factory
from models.billing_event import BillingEvent


async def emit_billing_event(
    org_id: UUID,
    event_type: str,
    event_name: str,
    quantity: float = 1.0,
    unit: str = "call",
    dimensions: Dict[str, Any] | None = None,
) -> None:
    async with async_session_factory() as session:
        try:
            evt = BillingEvent(
                organization_id=org_id,
                event_type=event_type,
                event_name=event_name,
                quantity=quantity,
                unit=unit,
                dimensions=(dimensions or {}),
                status=0,
            )
            session.add(evt)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
