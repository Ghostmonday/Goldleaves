

"""Minimal settings stub for tests."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class _Secret:
	value: str | None
	def get_secret_value(self) -> str | None:
		return self.value

class Settings:
	stripe_secret_key = _Secret(None)
	stripe_webhook_secret = _Secret("whsec_test")
	jwt_secret = _Secret("secret")
	jwt_algorithm = "HS256"
	enable_docs = True
	allowed_origins = "*"
	environment = "test"
	app_name = "Goldleaves"
	is_development = True
	# Default database for tests; modules can override via environment if needed
	database_url = _Secret("sqlite:///:memory:")

settings = Settings()


