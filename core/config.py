from pydantic_settings import BaseSettings
from builtins import property, all
from pydantic import SecretStr, field_validator
from typing import List

class Settings(BaseSettings):
    app_name: str = "Gold Leaves"
    environment: str = "development"
    debug: bool = True
    enable_docs: bool = True

    database_url: SecretStr
    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    allowed_origins: str = "http://localhost:3000"
    verification_token_expire_hours: int = 24
    reset_token_expire_hours: int = 1

    # Stripe configuration
    stripe_secret_key: SecretStr = SecretStr("")
    stripe_publishable_key: str = ""
    stripe_webhook_secret: SecretStr = SecretStr("")

    @property
    def is_development(self):
        return self.environment == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

def validate_config() -> bool:
    return all([
        settings.jwt_secret.get_secret_value(),
        settings.database_url.get_secret_value()
    ])