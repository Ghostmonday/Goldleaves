

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
	"""Return a simple opaque token for tests."""
	exp = (datetime.utcnow() + (expires_delta or timedelta(minutes=15))).isoformat()
	return f"test-token.{data.get('sub','user')}.{exp}"

def require_permission(*args, **kwargs):  # used in some patches/mocks
	return True


