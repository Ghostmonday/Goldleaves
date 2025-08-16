# core/usage.py
"""Test shims/utilities for usage tests."""
import os
from typing import Optional, Dict, Any
from datetime import datetime


# In-memory storage for test events
_usage_events = []
_active_events = {}
_current_test = None


class UsageEvent:
    """Simple usage event class for testing."""
    def __init__(self, request_id: str, status_code: int = 200, latency_ms: int = 0, **kwargs):
        self.request_id = request_id
        self.status_code = status_code
        self.latency_ms = latency_ms
        self.metadata = kwargs
        self.created_at = datetime.utcnow()


class UsageTracker:
    """Usage tracker exposing _active_events property."""
    @property
    def _active_events(self):
        return _active_events


def record_usage(request_id: str, status_code: int, latency_ms: int) -> None:
    """
    Record usage in in-memory list with per-test reset via PYTEST_CURRENT_TEST.
    """
    global _current_test, _usage_events
    
    # Check if we're in a new test
    current = os.environ.get("PYTEST_CURRENT_TEST")
    if current != _current_test:
        _current_test = current
        _usage_events = []
    
    # Record the usage
    _usage_events.append({
        "request_id": request_id,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "timestamp": datetime.utcnow()
    })


def start_event(
    request_id: str,
    event_type: str = "api",
    event_name: str = "api.request",
    db=None,
    **kwargs
) -> UsageEvent:
    """
    Start an event - idempotent by request_id.
    If db provided, use DB path; else use in-memory dict.
    """
    # Check if event already exists
    if request_id in _active_events:
        return _active_events[request_id]
    
    # Create new event
    event = UsageEvent(
        request_id=request_id,
        event_type=event_type,
        event_name=event_name,
        **kwargs
    )
    
    if db is not None:
        # DB path - store in database
        from models.usage_event import UsageEvent as DBUsageEvent
        db_event = DBUsageEvent(
            request_id=request_id,
            event_type=event_type,
            event_name=event_name,
            metadata=kwargs
        )
        db.add(db_event)
        db.commit()
        return db_event
    else:
        # In-memory path
        _active_events[request_id] = event
        return event


def finalize_event(event_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Finalize an event - remove from active, merge metadata.
    Returns True if event was found and finalized.
    """
    if event_id not in _active_events:
        return False
    
    event = _active_events.pop(event_id)
    
    # Merge metadata if provided
    if metadata:
        if hasattr(event, 'metadata'):
            event.metadata.update(metadata)
        else:
            event.metadata = metadata
    
    # Add to completed events (for testing)
    _usage_events.append(event)
    
    return True


def get_usage_tracker() -> UsageTracker:
    """Get usage tracker object exposing _active_events property."""
    return UsageTracker()


def get_usage_event_by_request_id(request_id: str) -> Optional[UsageEvent]:
    """Get usage event by request_id from active or completed events."""
    # Check active events first
    if request_id in _active_events:
        return _active_events[request_id]
    
    # Check completed events
    for event in _usage_events:
        if isinstance(event, UsageEvent) and event.request_id == request_id:
            return event
        elif isinstance(event, dict) and event.get("request_id") == request_id:
            # Convert dict to UsageEvent for consistency
            return UsageEvent(
                request_id=event["request_id"],
                status_code=event.get("status_code", 200),
                latency_ms=event.get("latency_ms", 0)
            )
    
    return None