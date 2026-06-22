from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Insure Claims API"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: str = "sqlite:///./insure.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
