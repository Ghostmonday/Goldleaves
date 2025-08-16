"""Minimal dependency stubs for tests."""

from __future__ import annotations

from typing import Optional

from models.user import User


def get_current_active_user() -> User:
	# Return a simple active user
	u = User()
	setattr(u, "id", 1)
	setattr(u, "is_active", True)
	return u


def get_current_organization_id() -> int:
	# Fixed org id for tests
	return 1


