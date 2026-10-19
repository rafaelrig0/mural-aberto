from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.works.models import WorkStatus
from tests.helpers import make_category, make_work

ADMIN = "/api/v1/admin/categories"


def test_public_list_needs_no_auth(client: TestClient, db: Session) -> None:
    make_category(db, "Pintura")
    make_category(db, "Fotografia")
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    assert [c["name"] for c in response.json()] == ["Fotografia", "Pintura"]


def test_admin_crud(client: TestClient, auth: dict[str, str]) -> None:
    created = client.post(ADMIN, json={"name": "  Crônica "}, headers=auth)
    assert created.status_code == 201
    assert created.json()["slug"] == "cronica"
    category_id = created.json()["id"]

    updated = client.put(f"{ADMIN}/{category_id}", json={"name": "Arte de Rua"}, headers=auth)
    assert updated.json() == {"id": category_id, "name": "Arte de Rua", "slug": "arte-de-rua"}

    assert client.delete(f"{ADMIN}/{category_id}", headers=auth).status_code == 204
    assert (
        client.put(f"{ADMIN}/{category_id}", json={"name": "Outra"}, headers=auth).status_code
        == 404
    )


def test_duplicate_name_conflicts(client: TestClient, auth: dict[str, str]) -> None:
    client.post(ADMIN, json={"name": "Conto"}, headers=auth)
    assert client.post(ADMIN, json={"name": "Conto"}, headers=auth).status_code == 409


def test_name_without_letters_is_rejected(client: TestClient, auth: dict[str, str]) -> None:
    assert client.post(ADMIN, json={"name": "???"}, headers=auth).status_code == 422


def test_cannot_delete_category_with_works(
    client: TestClient, auth: dict[str, str], db: Session
) -> None:
    category = make_category(db)
    make_work(db, category, status=WorkStatus.PENDING)
    response = client.delete(f"{ADMIN}/{category.id}", headers=auth)
    assert response.status_code == 409


def test_write_endpoints_require_auth(client: TestClient) -> None:
    assert client.post(ADMIN, json={"name": "Conto"}).status_code == 401
    assert client.put(f"{ADMIN}/1", json={"name": "Conto"}).status_code == 401
    assert client.delete(f"{ADMIN}/1").status_code == 401
