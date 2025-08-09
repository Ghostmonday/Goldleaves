"""Core usage tracking functionality."""

from typing import Dict, Any, Optional, List
from copy import deepcopy

# In-memory event storage for testing
_EVENTS: List[Dict[str, Any]] = []


def record_usage(
    request_id: str, 
    status_code: int, 
    latency_ms: int, 
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Record a usage event with request metrics.
    
    Args:
        request_id: Unique identifier for the request
        status_code: HTTP status code of the response
        latency_ms: Request processing time in milliseconds
        extra: Optional additional data to include in the event
        
    Returns:
        The recorded event dictionary
    """
    # Derive result based on status code
    result = "success" if status_code < 400 else "error"
    
    # Build event dictionary
    event = {
        "request_id": request_id,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "result": result
    }
    
    # Merge any extra data
    if extra:
        event.update(extra)
    
    # Append to in-memory storage
    _EVENTS.append(event)
    
    return event


def get_events() -> List[Dict[str, Any]]:
    """Get a copy of all recorded usage events.
    
    Returns:
        List of event dictionaries
    """
    return deepcopy(_EVENTS)


def reset_events() -> None:
    """Clear all recorded usage events."""
    global _EVENTS
    _EVENTS.clear()