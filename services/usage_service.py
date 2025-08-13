"""Minimal usage service to emit billing events (PR-1)."""
from __future__ import annotations

from typing import Any, Dict
from sqlalchemy.orm import Session

from core.db.session import get_db, Base
from models.billing_event import BillingEvent


async def emit_billing_event(
    org_id: int,
    event_type: str,
    event_name: str,
    quantity: float = 1.0,
    unit: str = "call",
    dimensions: Dict[str, Any] | None = None,
) -> None:
    # Use sync session for now; tests run on SQLite
    db: Session = next(get_db())
    try:
        # Ensure tables exist in ephemeral SQLite test DBs
        try:
            bind = db.get_bind()
            Base.metadata.create_all(bind)
        except Exception:
            pass
        evt = BillingEvent(
            organization_id=org_id,
            event_type=event_type,
            event_name=event_name,
            quantity=quantity,
            unit=unit,
            dimensions=dimensions or {},
            status=0,
        )
        db.add(evt)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
    finally:
        db.close()
