# models/billing_event.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, JSON, Index
from sqlalchemy.sql import func
from core.db.session import Base


class BillingEvent(Base):
    __tablename__ = "billing_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, index=True)
    event_type = Column(String(40))
    event_name = Column(String(64), index=True)
    resource_id = Column(String(64), nullable=True)
    quantity = Column(Numeric(12, 4), default=1.0)
    unit = Column(String(16), default="call")
    unit_cost_cents = Column(Integer, nullable=True)
    dimensions = Column(JSON)
    status = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('ix_billing_events_org_created', 'organization_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<BillingEvent(id={self.id}, event_name={self.event_name})>"