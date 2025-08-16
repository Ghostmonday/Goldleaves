# services/usage_service.py
from typing import Optional
from models.billing_event import BillingEvent
from core.db.session import get_db


def emit_billing_event(
    org_id: int,
    event_type: str,
    event_name: str,
    quantity: float = 1.0,
    unit: str = "call",
    dimensions: Optional[dict] = None
) -> None:
    """
    Emit a billing event to the database.
    Uses sync session from core.db.session.get_db.
    """
    db = next(get_db())
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
        db.commit()
    except Exception as e:
        # Rollback on error
        db.rollback()
        raise e
    finally:
        # Close session
        db.close()