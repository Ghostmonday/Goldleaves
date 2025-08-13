# Minimal models module to satisfy imports in tests
from models.user import User  # re-export


class RefreshToken:
    def __init__(self, user_id: int | None = None, token: str | None = None, expires_at=None, is_active: bool = True):
        self.id = None
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at
        self.is_active = is_active
