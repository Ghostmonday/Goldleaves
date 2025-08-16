# services/usage_service.py
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from models.billing_event import BillingEvent
from core.db.session import async_session_factory


async def emit_billing_event(
    org_id: UUID,
    event_type: str,
    event_name: str,
    quantity: float = 1.0,
    unit: str = "call",
    dimensions: Optional[dict] = None
) -> None:
    """
    Emit a billing event to the database asynchronously.
    Uses async session from core.db.session.async_session_factory.
    """
    async with async_session_factory() as db:
        try:
            # Create billing event
            billing_event = BillingEvent(
                organization_id=org_id,
                event_type=event_type,
                event_name=event_name,
                quantity=quantity,
                unit=unit,
                dimensions=dimensions or {}
            )
            
            # Add to session and commit
            db.add(billing_event)
            await db.commit()
        except Exception as e:
            # Rollback on error
            await db.rollback()
            raise e