from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.modules.admins.models import Admin
from tests.helpers import ADMIN_EMAIL, ADMIN_PASSWORD

LOGIN = "/api/v1/auth/login"


def test_login_success_returns_bearer_token(client: TestClient, admin: Admin) -> None:
    response = client.post(LOGIN, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.json()["email"] == ADMIN_EMAIL


def test_login_email_is_case_insensitive(client: TestClient, admin: Admin) -> None:
    response = client.post(LOGIN, json={"email": "ADMIN@Example.com", "password": ADMIN_PASSWORD})
    assert response.status_code == 200


def test_wrong_password_and_unknown_email_look_identical(client: TestClient, admin: Admin) -> None:
    wrong_password = client.post(LOGIN, json={"email": ADMIN_EMAIL, "password": "errada-errada"})
    unknown_email = client.post(LOGIN, json={"email": "x@example.com", "password": "errada-errada"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_inactive_admin_cannot_login_nor_use_old_token(
    client: TestClient, admin: Admin, auth: dict[str, str], db: Session
) -> None:
    db_admin = db.get(Admin, admin.id)
    assert db_admin is not None
    db_admin.is_active = False
    db.commit()
    assert client.get("/api/v1/auth/me", headers=auth).status_code == 401
    response = client.post(LOGIN, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert response.status_code == 401


def test_admin_routes_reject_missing_invalid_and_expired_tokens(
    client: TestClient, admin: Admin
) -> None:
    secret = get_settings().jwt_secret_key.get_secret_value()
    expired = jwt.encode(
        {"sub": str(admin.id), "exp": datetime.now(UTC) - timedelta(seconds=5)},
        secret,
        algorithm="HS256",
    )
    for headers in ({}, {"Authorization": "Bearer lixo"}, {"Authorization": f"Bearer {expired}"}):
        assert client.get("/api/v1/admin/works", headers=headers).status_code == 401


def test_login_is_rate_limited(client: TestClient, admin: Admin) -> None:
    limiter.enabled = True
    limiter.reset()
    try:
        codes = [
            client.post(LOGIN, json={"email": ADMIN_EMAIL, "password": "errada-errada"}).status_code
            for _ in range(7)
        ]
    finally:
        limiter.enabled = False
    assert codes[:5] == [401] * 5
    assert codes[5:] == [429, 429]


def test_login_validation_error_has_standard_shape_and_no_input_echo(client: TestClient) -> None:
    response = client.post(LOGIN, json={"email": "nao-e-email", "password": "segredo-enviado"})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert "segredo-enviado" not in response.text


def test_create_admin_rejects_invalid_email(db: Session) -> None:
    """Regressão: o script aceitava 'admin' e criava uma conta que nunca conseguia logar."""
    import pytest

    from app.core.exceptions import UnprocessableError
    from app.modules.admins.service import create_admin

    with pytest.raises(UnprocessableError):
        create_admin(db, "admin", "senha-super-segura-123")
