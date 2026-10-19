from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.modules.categories.service import slugify


def test_password_hash_is_not_plaintext_and_verifies() -> None:
    hashed = hash_password("uma-senha-longa-123")
    assert "uma-senha" not in hashed
    assert verify_password("uma-senha-longa-123", hashed)
    assert not verify_password("outra-senha", hashed)


def test_verify_password_without_hash_is_always_false() -> None:
    assert not verify_password("qualquer", None)


def test_token_roundtrip() -> None:
    token, expires_in = create_access_token(42)
    assert decode_access_token(token) == 42
    assert expires_in == get_settings().jwt_expire_minutes * 60


def test_expired_and_tampered_tokens_are_rejected() -> None:
    settings = get_settings()
    secret = settings.jwt_secret_key.get_secret_value()
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=1)}, secret, algorithm="HS256"
    )
    wrong_key = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) + timedelta(minutes=5)}, "x" * 40, algorithm="HS256"
    )
    no_expiry = jwt.encode({"sub": "1"}, secret, algorithm="HS256")
    assert decode_access_token(expired) is None
    assert decode_access_token(wrong_key) is None
    assert decode_access_token(no_expiry) is None
    assert decode_access_token("lixo") is None


def test_slugify() -> None:
    assert slugify("Crônica") == "cronica"
    assert slugify("  Arte  de   Rua! ") == "arte-de-rua"
    assert slugify("???") == ""
