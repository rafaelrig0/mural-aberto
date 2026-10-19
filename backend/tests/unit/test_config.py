import pytest
from pydantic import ValidationError

from app.core.config import Settings

VALID = {
    "database_url": "postgresql://u:p@host:5432/db",
    "jwt_secret_key": "x" * 40,
    "supabase_url": "https://proj.supabase.co/",
    "supabase_service_role_key": "key",
}


def make(**overrides: object) -> Settings:
    return Settings(_env_file=None, **{**VALID, **overrides})  # type: ignore[arg-type]


def test_database_url_is_normalized_to_psycopg_driver() -> None:
    assert make().database_url == "postgresql+psycopg://u:p@host:5432/db"
    assert make(database_url="postgres://u:p@h/db").database_url == "postgresql+psycopg://u:p@h/db"


def test_supabase_url_loses_trailing_slash() -> None:
    assert make().supabase_url == "https://proj.supabase.co"


def test_short_jwt_secret_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make(jwt_secret_key="curta")


def test_secrets_are_not_leaked_in_repr() -> None:
    assert "x" * 40 not in repr(make())


@pytest.mark.parametrize("origins", [[], ["*"]])
def test_production_requires_explicit_cors(origins: list[str]) -> None:
    with pytest.raises(ValidationError):
        make(environment="production", cors_origins=origins)


def test_production_with_explicit_cors_is_valid() -> None:
    settings = make(environment="production", cors_origins=["https://site.com"])
    assert settings.is_production


def test_size_limits_in_bytes() -> None:
    settings = make(max_image_size_mb=2, max_video_size_mb=3)
    assert settings.max_image_size_bytes == 2 * 1024 * 1024
    assert settings.max_video_size_bytes == 3 * 1024 * 1024
