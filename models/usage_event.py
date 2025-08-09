"""Usage event data models."""

from typing import Literal
from pydantic import BaseModel


class UsageEvent(BaseModel):
    """Model for usage event data with request metrics."""
    
    request_id: str
    status_code: int
    latency_ms: int
    result: Literal["success", "error"]