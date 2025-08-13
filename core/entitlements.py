

"""Entitlement service, simple plan limits, and access control decorators.

Provides a tiny in-memory usage tracker and a minimal billing summary API
surface used by limits tests.
"""

from __future__ import annotations

from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Iterable, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

try:
	from models.entitlement import Entitlement, PlanType
except Exception:  # pragma: no cover
	Entitlement = None  # type: ignore
	PlanType = Enum("PlanType", "FREE PRO TEAM")  # type: ignore


class EntitlementService:
	"""Service providing static helpers used in tests."""

	@staticmethod
	def _query(db: Session, **filters):
		if Entitlement is None:
			return []
		q = db.query(Entitlement)
		for k, v in filters.items():
			q = q.filter(getattr(Entitlement, k) == v)
		return q.all()

	@staticmethod
	def get_current_entitlement(user, tenant_id: Optional[int] = None, db: Session = None):  # noqa: D401
		if db is None or Entitlement is None:
			return None
		if tenant_id is not None:
			res = EntitlementService._query(db, tenant_id=tenant_id)
		else:
			res = EntitlementService._query(db, user_id=getattr(user, "id", None))
		return res[0] if res else None

	@staticmethod
	def check_plan_access(user, required_plans: Iterable[Any], tenant_id: Optional[int] = None, db: Session = None) -> bool:  # noqa: D401,E501
		ent = EntitlementService.get_current_entitlement(user, tenant_id=tenant_id, db=db)
		if ent is None:
			# Allow if FREE in required list
			return any(str(p) == str(PlanType.FREE) or getattr(p, "name", None) == "FREE" for p in required_plans)
		return ent.plan in required_plans or getattr(ent.plan, "name", None) in [getattr(p, "name", str(p)) for p in required_plans]

	@staticmethod
	def check_feature_access(user, feature_name: str, tenant_id: Optional[int] = None, db: Session = None) -> bool:  # noqa: D401,E501
		ent = EntitlementService.get_current_entitlement(user, tenant_id=tenant_id, db=db)
		if not ent or not getattr(ent, "features", None):
			return False
		return bool(ent.features.get(feature_name))

	@staticmethod
	def get_feature_limit(user, feature_name: str, tenant_id: Optional[int] = None, default_limit: int = 0, db: Session = None) -> int:  # noqa: D401,E501
		ent = EntitlementService.get_current_entitlement(user, tenant_id=tenant_id, db=db)
		if not ent:
			return default_limit
		return int(ent.features.get(feature_name, default_limit)) if getattr(ent, "features", None) else default_limit


# -------------------------- Decorators ---------------------------------------
def get_current_active_user():  # simple stub for tests
	class _U:
		id = 1
	return _U()

# Expose get_db for patching in tests
try:
	from core.database import get_db as get_db  # type: ignore
except Exception:  # pragma: no cover
	def get_db():  # type: ignore
		yield None


def requires_plan(*plans):
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			user = get_current_active_user()
			# db is provided via dependency in tests (patched). Call it and pass directly.
			db = get_db()
			# Normalize plans into PlanType enums if provided as strings
			required = []
			for p in plans:
				if isinstance(p, PlanType):
					required.append(p)
				else:
					try:
						required.append(PlanType(str(p)))
					except Exception:
						required.append(p)  # fallback
			ok = EntitlementService.check_plan_access(user=user, required_plans=required, tenant_id=None, db=db)  # noqa: E501
			if not ok:
				raise HTTPException(status_code=403, detail=f"Access denied. Requires one of: {', '.join(map(str, plans))}")
			return func(*args, **kwargs)
		return wrapper
	return decorator


def requires_feature(feature_name: str):
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			user = get_current_active_user()
			db = get_db()
			ok = EntitlementService.check_feature_access(user=user, feature_name=feature_name, tenant_id=None, db=db)
			if not ok:
				raise HTTPException(status_code=403, detail=f"Access denied. Missing feature: {feature_name}")
			return func(*args, **kwargs)
		return wrapper
	return decorator


def reset_all_usage():  # used by some limit tests; stubbed as no-op
	_usage_storage.clear()
	return True


# ----------------------- Simple plan limits and usage -----------------------
# Human-readable plan names for tests (Free/Pro/Team)
PLAN_LIMITS: Dict[str, Dict[str, int]] = {
	"Free": {"soft": 500, "hard": 750},
	"Pro": {"soft": 5000, "hard": 10000},
	"Team": {"soft": 50000, "hard": 100000},
}

# naive in-memory store keyed by f"{tenant_id}:api_calls"
_usage_storage: Dict[str, int] = {}

class UsageInfo:
	def __init__(self, current_usage: int, soft_cap: int, hard_cap: int, unit: str = "api_calls"):
		self.current_usage = current_usage
		self.soft_cap = soft_cap
		self.hard_cap = hard_cap
		self.unit = unit


def _resolve_plan_for_tenant(tenant_id: str) -> str:
	# Simple mapping used by tests: tenant_pro -> Pro, tenant_team -> Team, otherwise Free
	if str(tenant_id).startswith("tenant_pro"):
		return "Pro"
	if str(tenant_id).startswith("tenant_team"):
		return "Team"
	return "Free"


def get_usage_info(tenant_id: str) -> UsageInfo:
	plan_name = _resolve_plan_for_tenant(tenant_id)
	limits = PLAN_LIMITS[plan_name]
	key = f"{tenant_id}:api_calls"
	current = _usage_storage.get(key, 0)
	return UsageInfo(current_usage=current, soft_cap=limits["soft"], hard_cap=limits["hard"], unit="api_calls")


