# models/billing_event.py
from sqlalchemy import Column, String, Numeric, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
import uuid
from core.db.session import Base


class BillingEvent(Base):
    __tablename__ = "billing_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), index=True)
    event_type = Column(String(40))
    event_name = Column(String(64), index=True)
    resource_id = Column(String(64), nullable=True)
    quantity = Column(Numeric(12, 4), default=1.0)
    unit = Column(String(16), default="call")
    unit_cost_cents = Column(Integer, nullable=True)
    dimensions = Column(JSONB, default={})
    status = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('ix_billing_events_org_created', 'organization_id', 'created_at'),
        Index('ix_billing_events_dimensions', 'dimensions', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<BillingEvent(id={self.id}, event_name={self.event_name})>"