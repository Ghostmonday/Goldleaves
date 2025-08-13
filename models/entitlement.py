

"""Entitlement model stubs for tests."""

from __future__ import annotations

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.types import JSON
from enum import Enum

from core.database import Base

class PlanType(str, Enum):
	FREE = "free"
	PRO = "pro"
	TEAM = "team"

class Entitlement(Base):
	__tablename__ = "entitlements"
	id = Column(Integer, primary_key=True, autoincrement=True)
	user_id = Column(Integer, nullable=True, index=True)
	tenant_id = Column(Integer, nullable=True, index=True)
	plan = Column(String(20), nullable=False, default=PlanType.FREE.value)
	features = Column(JSON, nullable=True, default=dict)
	active = Column(Boolean, nullable=False, default=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now())
	updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
	# Stripe integration fields used in tests
	stripe_customer_id = Column(String(100), nullable=True)
	stripe_subscription_id = Column(String(100), nullable=True)

	@staticmethod
	def get_default_features(plan: PlanType):  # simple defaults
		if plan == PlanType.PRO or str(plan).lower() == "pro":
			return {"api_requests_per_month": 50000, "storage_gb": 100}
		if plan == PlanType.TEAM or str(plan).lower() == "team":
			return {"api_requests_per_month": 200000, "storage_gb": 500}
		return {"api_requests_per_month": 1000, "storage_gb": 5}

	def activate(self):
		self.active = True

	def deactivate(self):
		self.active = False


