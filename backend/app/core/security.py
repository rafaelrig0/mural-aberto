from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

_hasher = PasswordHasher()
# Hash descartável: permite gastar o mesmo tempo ao verificar um e-mail inexistente,
# para o tempo de resposta do login não revelar quais e-mails existem.
_DUMMY_HASH = _hasher.hash("senha-descartavel-para-igualar-tempo")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(admin_id: int) -> tuple[str, int]:
    """Devolve (token, segundos até expirar)."""
    settings = get_settings()
    now = datetime.now(UTC)
    expires_in = settings.jwt_expire_minutes * 60
    payload = {"sub": str(admin_id), "iat": now, "exp": now + timedelta(seconds=expires_in)}
    token = jwt.encode(
        payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm
    )
    return token, expires_in


def decode_access_token(token: str) -> int | None:
    """Devolve o id do admin, ou None se o token for inválido ou estiver expirado."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        return None
