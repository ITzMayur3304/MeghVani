from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    frontend_origins: str = "http://localhost:3000,http://localhost:5173"
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    openweather_api_key: str | None = None
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "MeghVaani/0.1"
    tweetharvest_api_url: str | None = None
    tweetharvest_api_key: str | None = None
    tweetharvest_bearer_token: str | None = None
    jwt_secret: str | None = None
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5/weather"
    openweather_poll_interval_seconds: int = Field(default=900, ge=60, le=86400)
    admin_username: str | None = None
    admin_password_hash: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.frontend_origins.split(",") if item.strip()]

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
