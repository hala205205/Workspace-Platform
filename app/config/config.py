from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Workspace Platform API"
    environment: str = "development"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./workspace.db"
    jwt_secret: str = Field(default="development-only-change-this-secret-now", min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:3000"
    upload_dir: Path = Path("uploads")
    max_upload_size_mb: int = 10

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def validate_production(self) -> None:
        if self.environment == "production" and "development-only" in self.jwt_secret:
            raise RuntimeError("JWT_SECRET must be configured in production")


@lru_cache
def get_settings() -> Settings:
    result = Settings()
    result.validate_production()
    return result


settings = get_settings()
