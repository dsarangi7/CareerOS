from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CAREEROS_", env_file=".env", extra="ignore")

    env: str = "local"
    database_url: str = "sqlite:///./career_os.db"
    log_level: str = "INFO"
    max_upload_mb: int = Field(default=10, ge=1, le=100)


@lru_cache
def get_settings() -> Settings:
    return Settings()
