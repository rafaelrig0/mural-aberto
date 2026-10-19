import os
from collections.abc import Iterator
from urllib.parse import urlparse

# --- Ambiente de teste: definido ANTES de importar a aplicação ---------------------------------
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5433/catalog_test"
)
# Trava de segurança: os testes apagam todas as tabelas. Nunca rodar contra outro banco.
if not urlparse(TEST_DATABASE_URL).path.rstrip("/").endswith("_test"):
    raise RuntimeError("TEST_DATABASE_URL deve apontar para um banco cujo nome termina em '_test'.")

os.environ.update(
    ENVIRONMENT="test",
    DATABASE_URL=TEST_DATABASE_URL,
    JWT_SECRET_KEY="chave-de-testes-com-mais-de-trinta-e-dois-caracteres",
    SUPABASE_URL="https://test.supabase.co",
    SUPABASE_SERVICE_ROLE_KEY="chave-de-teste",
    CORS_ORIGINS='["http://localhost:5173"]',
    MAX_IMAGE_SIZE_MB="1",  # limites pequenos para testar estouro sem arquivos enormes
    MAX_VIDEO_SIZE_MB="2",
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.admins.models import Admin  # noqa: E402
from app.modules.admins.service import create_admin  # noqa: E402
from app.modules.media.storage import get_storage_service  # noqa: E402
from tests.helpers import ADMIN_EMAIL, ADMIN_PASSWORD, FakeStorage  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema() -> Iterator[None]:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables() -> None:
    tables = ", ".join(f'"{name}"' for name in Base.metadata.tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture
def client(storage: FakeStorage) -> Iterator[TestClient]:
    app.dependency_overrides[get_storage_service] = lambda: storage
    limiter.enabled = False
    limiter.reset()
    # raise_server_exceptions=False: erros 500 viram resposta HTTP, como em produção
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin(db: Session) -> Admin:
    return create_admin(db, ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture
def auth(client: TestClient, admin: Admin) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
