
"""Core usage tracking utilities for tests (in-memory)."""
from __future__ import annotations

from typing import Dict, Any, List, Optional
import uuid
import os

from models.usage_event import UsageEvent


# In-memory event store for latency tests
_events: List[Dict[str, Any]] = []
# Track current pytest test id to auto-clear between tests
_current_test_id: Optional[str] = None


def record_usage(request_id: str, status_code: int, latency_ms: int) -> None:
	"""Record a simple usage event for latency tracking tests."""
	# If running under pytest, auto-reset when the test changes to avoid cross-test leakage
	global _current_test_id
	pytest_id = os.environ.get("PYTEST_CURRENT_TEST")
	if pytest_id is not None and pytest_id != _current_test_id:
		_events.clear()
		_current_test_id = pytest_id
	result = "success" if 200 <= status_code < 400 else "error"
	_events.append(
		{
			"request_id": request_id,
			"status_code": status_code,
			"latency_ms": max(0, int(latency_ms)),
			"result": result,
		}
	)


def get_events() -> List[Dict[str, Any]]:
	return list(_events)


def reset_events() -> None:
	_events.clear()


# Active events keyed by request_id for idempotency
_active_by_request_id: Dict[str, UsageEvent] = {}


class _UsageTracker:
	def __init__(self) -> None:
		self._active_events: Dict[str, UsageEvent] = _active_by_request_id


_tracker = _UsageTracker()


def start_event(
	*,
	route: str,
	action: str,
	request_id: Optional[str] = None,
	user_id: Optional[str] = None,
	tenant_id: Optional[str] = None,
	units: float | None = None,
	db: Any = None,  # accepted for signature compatibility
) -> UsageEvent:
	"""Create or return an idempotent UsageEvent keyed by request_id.

	If a DB session is provided, persist and dedupe by request_id in the database.
	Otherwise, keep an in-memory active event for idempotency during tests.
	"""
	rid = request_id or uuid.uuid4().hex
	# DB-backed idempotency
	if db is not None:
		existing = UsageEvent.get_by_request_id(db, rid)
		if existing:
			return existing
		# Create and persist a new event
		ev = UsageEvent(
			request_id=rid,
			tenant_id=tenant_id,
			user_id=user_id,
			route=route,
			action=action,
			units=units if units is not None else 1.0,
		)
		db.add(ev)
		db.commit()
		db.refresh(ev)
		return ev

	# In-memory idempotency for tests without DB
	if rid in _active_by_request_id:
		return _active_by_request_id[rid]
	ev = UsageEvent(
		request_id=rid,
		tenant_id=tenant_id,
		user_id=user_id,
		route=route,
		action=action,
		units=units if units is not None else 1.0,
	)
	_active_by_request_id[rid] = ev
	return ev


def get_usage_event_by_request_id(request_id: str) -> Optional[UsageEvent]:
	return _active_by_request_id.get(request_id)


# Shims for tests expecting these symbols
def get_usage_tracker() -> _UsageTracker:
	return _tracker


async def finalize_event(event_id: str, metadata: Dict[str, Any] | None = None) -> bool:
	"""Finalize an in-memory event and apply metadata; returns True if existed."""
	ev = _active_by_request_id.pop(event_id, None)
	if not ev:
		return False
	if metadata:
		# type: ignore[attr-defined]
		if getattr(ev, "metadata", None) is None:
			setattr(ev, "metadata", {})
		# type: ignore[index]
		ev.metadata.update(metadata)
	return True


