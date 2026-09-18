from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ENGLISH7_",
        extra="ignore",
    )

    service_name: str = "english7-api"
    api_prefix: str = "/api/v1"
    database_url: SecretStr | None = None
    jwt_secret: SecretStr | None = None
    jwt_algorithm: str | None = None
    access_token_minutes: int | None = None

    def require_database_url(self) -> str:
        if self.database_url is None:
            raise RuntimeError("ENGLISH7_DATABASE_URL is required for database access")
        return self.database_url.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()
