

"""Router contract constants & simple status enum for tests."""

from __future__ import annotations

from enum import Enum

class RouterTags(str, Enum):  # minimal set used in tests
	USAGE = "Usage"
	BILLING = "Billing"

class HTTPStatus:
	OK = 200
	BAD_REQUEST = 400
	UNAUTHORIZED = 401
	FORBIDDEN = 403
	NOT_FOUND = 404
	INTERNAL_SERVER_ERROR = 500


