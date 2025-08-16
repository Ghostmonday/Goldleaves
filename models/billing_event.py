"""BillingEvent model using GUID/JSONBCompat with safe defaults (cross-dialect)."""
from __future__ import annotations

import uuid
from sqlalchemy import Column, String, Numeric, Integer, Index, ForeignKey, text
from typing import Optional, Any, cast
from decimal import Decimal
from datetime import datetime
from sqlalchemy.types import TIMESTAMP

from core.db.session import Base
from core.db.types import GUID, JSONBCompat


class BillingEvent(Base):
    __tablename__ = "billing_events"

    id: Column[GUID] = Column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Column[Optional[GUID]] = cast(
        Column[Optional[GUID]],
        Column(GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), index=True),
    )
    event_type: Column[str] = Column(String(40))
    event_name: Column[str] = Column(String(64), index=True)
    resource_id: Column[Optional[str]] = cast(
        Column[Optional[str]], Column(String(64), nullable=True)
    )
    quantity: Column[Decimal] = Column(Numeric(12, 4), default=Decimal("1.0"))
    unit: Column[str] = Column(String(16), default="call")
    unit_cost_cents: Column[Optional[int]] = cast(
        Column[Optional[int]], Column(Integer, nullable=True)
    )
    dimensions: Column[Any] = Column(JSONBCompat, default=dict)
    status: Column[int] = Column(Integer, default=0)
    created_at: Column[datetime] = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        Index("ix_billing_events_org_created", "organization_id", "created_at"),
        Index("ix_billing_events_dimensions", "dimensions", postgresql_using="gin"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<BillingEvent id={self.id} name={self.event_name}>"
