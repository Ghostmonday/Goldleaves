
"""UsageEvent SQLAlchemy model used in middleware tests."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import Session

from models.base import Base


class UsageEvent(Base):
	__tablename__ = "usage_events"

	id = Column(Integer, primary_key=True, autoincrement=True)
	request_id = Column(String(255), unique=True, index=True, nullable=False)
	tenant_id = Column(String(255), index=True, nullable=True)
	user_id = Column(String(255), index=True, nullable=True)
	route = Column(String(512), nullable=False)
	action = Column(String(64), nullable=False)
	units = Column(Float, nullable=False, default=1.0)
	cost_cents = Column(Integer, nullable=True)
	ts = Column(DateTime, nullable=False, default=datetime.utcnow)

	# --- Business helpers ---
	def calculate_cost(self, rate_cents: int) -> int:
		"""Calculate cost in cents for this event (units * rate)."""
		cents = int(self.units * rate_cents)
		self.cost_cents = cents
		return cents

	@classmethod
	def get_by_request_id(cls, db: Session, request_id: str) -> Optional["UsageEvent"]:
		return db.query(cls).filter(cls.request_id == request_id).first()

	@classmethod
	def get_usage_summary(
		cls,
		db: Session,
		tenant_id: str,
		start_date: datetime,
		end_date: datetime,
	) -> Dict[str, Any]:
		q = db.query(cls).filter(
			cls.tenant_id == tenant_id,
			cls.ts >= start_date,
			cls.ts <= end_date,
		)
		total_events = q.count()
		total_units = float(q.with_entities(func.coalesce(func.sum(cls.units), 0)).scalar() or 0)
		total_cost = int(q.with_entities(func.coalesce(func.sum(cls.cost_cents), 0)).scalar() or 0)
		unique_routes = int(q.with_entities(func.count(func.distinct(cls.route))).scalar() or 0)

		return {
			"tenant_id": tenant_id,
			"total_events": total_events,
			"total_units": total_units,
			"total_cost_cents": total_cost,
			"unique_routes": unique_routes,
		}

	def __repr__(self) -> str:  # pragma: no cover simple repr
		return f"<UsageEvent id={self.id} route={self.route} action={self.action} request_id={self.request_id}>"


