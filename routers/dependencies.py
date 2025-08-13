

"""Router-level dependency stubs used in tests."""
from __future__ import annotations
from typing import Dict, Any
from fastapi import HTTPException
from .contract import HTTPStatus

def get_current_user() -> Dict[str, Any]:
	# Default behavior: unauthorized unless patched in tests
	raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Unauthorized")

def get_tenant_context() -> Dict[str, Any]:
	raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Unauthorized")


