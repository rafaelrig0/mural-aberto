from functools import lru_cache
from typing import Literal, Self

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_JWT_SECRET_LENGTH = 32
BYTES_PER_MB = 1024 * 1024


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    database_url: str
    cors_origins: list[str] = []

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    supabase_url: str
    supabase_service_role_key: SecretStr
    supabase_bucket: str = "works-media"
    signed_url_expire_seconds: int = 3600

    max_image_size_mb: int = 10
    max_video_size_mb: int = 50

    rate_limit_login: str = "5/minute"
    rate_limit_submit_work: str = "10/hour"
    rate_limit_submit_comment: str = "20/hour"
    rate_limit_submit_feedback: str = "10/hour"

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        """O Supabase fornece 'postgresql://', que o SQLAlchemy associaria ao psycopg2."""
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value

    @field_validator("supabase_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("jwt_secret_key")
    @classmethod
    def jwt_secret_must_be_long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_JWT_SECRET_LENGTH:
            raise ValueError(f"JWT_SECRET_KEY deve ter ao menos {MIN_JWT_SECRET_LENGTH} caracteres")
        return value

    @model_validator(mode="after")
    def production_cors_must_be_explicit(self) -> Self:
        if self.environment == "production" and (not self.cors_origins or "*" in self.cors_origins):
            raise ValueError("Em produção, CORS_ORIGINS deve listar origens explícitas (sem '*')")
        return self

    @property
    def max_image_size_bytes(self) -> int:
        return self.max_image_size_mb * BYTES_PER_MB

    @property
    def max_video_size_bytes(self) -> int:
        return self.max_video_size_mb * BYTES_PER_MB

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
