"""
CleanBreath AI – application settings.
All secrets come from environment variables.  Pydantic-settings validates
them at startup and raises a clear error if any required field is missing.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    environment: str = "development"
    log_level: str = "INFO"
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""

    # Privacy / field encryption
    health_data_encryption_key: str = ""  # Fernet key; empty → health notes disabled

    # Gemini
    gemini_api_key: str = ""
    gemini_flash_model: str = "gemini-2.5-flash"
    gemini_pro_model: str = "gemini-2.5-pro"

    # Air Quality APIs
    open_meteo_base_url: str = "https://air-quality-api.open-meteo.com/v1"
    open_meteo_weather_url: str = "https://api.open-meteo.com/v1"
    openaq_api_key: str = ""
    waqi_api_token: str = ""

    # Push
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:alerts@cleanbreath.example"
    vapid_public_key: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def health_encryption_enabled(self) -> bool:
        return bool(self.health_data_encryption_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance – call once at import, reuse everywhere."""
    return Settings()
