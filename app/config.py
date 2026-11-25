from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    admin_id: int
    database_url: str
    app_name: str = "Universal Media"
    log_level: str = "INFO"
    audd_api_token: str | None = None
    max_media_file_mb: int = Field(default=15, ge=1, le=25)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
