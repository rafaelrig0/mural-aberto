from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.comments.models import CommentStatus
from app.modules.works.models import WorkStatus, WorkType
from tests.helpers import make_category, make_comment, make_work

WORKS = "/api/v1/works"


def test_only_approved_works_are_listed(client: TestClient, db: Session) -> None:
    category = make_category(db)
    make_work(db, category, title="Aprovada")
    for status in (WorkStatus.PENDING, WorkStatus.REJECTED, WorkStatus.ARCHIVED):
        make_work(db, category, status=status, title=f"Obra {status.value}")
    body = client.get(WORKS).json()
    assert [w["title"] for w in body["items"]] == ["Aprovada"]
    assert body["total"] == 1


def test_public_payload_never_exposes_private_data(client: TestClient, db: Session) -> None:
    category = make_category(db)
    work = make_work(db, category, with_image=True, work_type=WorkType.VISUAL)
    for response in (client.get(WORKS), client.get(f"{WORKS}/{work.id}")):
        assert "contact_email" not in response.text
        assert "maria@privado.com" not in response.text
        assert "storage_path" not in response.text
        assert "rejection_reason" not in response.text
        assert "usage_authorized" not in response.text


def test_media_is_returned_as_signed_urls(client: TestClient, db: Session) -> None:
    category = make_category(db)
    work = make_work(db, category, with_image=True, work_type=WorkType.VISUAL)
    detail = client.get(f"{WORKS}/{work.id}").json()
    assert detail["image_url"].startswith("https://signed.example/works/")
    assert detail["video_url"] is None


def test_non_approved_work_detail_is_404(client: TestClient, db: Session) -> None:
    category = make_category(db)
    for status in (WorkStatus.PENDING, WorkStatus.REJECTED, WorkStatus.ARCHIVED):
        work = make_work(db, category, status=status)
        assert client.get(f"{WORKS}/{work.id}").status_code == 404
    assert client.get(f"{WORKS}/9999").status_code == 404


def test_detail_shows_only_approved_comments(client: TestClient, db: Session) -> None:
    category = make_category(db)
    work = make_work(db, category)
    make_comment(db, work, CommentStatus.APPROVED, "visível")
    make_comment(db, work, CommentStatus.PENDING, "pendente")
    make_comment(db, work, CommentStatus.REJECTED, "rejeitado")
    comments = client.get(f"{WORKS}/{work.id}").json()["comments"]
    assert [c["content"] for c in comments] == ["visível"]


def test_filters_search_and_pagination(client: TestClient, db: Session) -> None:
    photos, poems = make_category(db, "Fotografia"), make_category(db, "Poema")
    for i in range(5):
        make_work(db, poems, title=f"Poema {i}", author_name="Carlos")
    make_work(db, photos, title="100% Sol_aberto", author_name="Lia", work_type=WorkType.VISUAL)

    assert client.get(WORKS, params={"category_id": photos.id}).json()["total"] == 1
    assert client.get(WORKS, params={"work_type": "text"}).json()["total"] == 5
    assert client.get(WORKS, params={"q": "carlos"}).json()["total"] == 5
    # curingas do LIKE são tratados como texto literal
    assert client.get(WORKS, params={"q": "100%"}).json()["total"] == 1
    assert client.get(WORKS, params={"q": "%"}).json()["total"] == 1
    assert client.get(WORKS, params={"q": "_"}).json()["total"] == 1

    page = client.get(WORKS, params={"page": 2, "page_size": 4}).json()
    assert (page["total"], page["page"], page["page_size"], len(page["items"])) == (6, 2, 4, 2)


def test_newest_approved_first(client: TestClient, db: Session) -> None:
    category = make_category(db)
    make_work(db, category, title="Primeira")
    make_work(db, category, title="Segunda")
    titles = [w["title"] for w in client.get(WORKS).json()["items"]]
    assert titles == ["Segunda", "Primeira"]


def test_invalid_pagination_params_are_422(client: TestClient) -> None:
    assert client.get(WORKS, params={"page": 0}).status_code == 422
    assert client.get(WORKS, params={"page_size": 1000}).status_code == 422


def test_list_does_not_run_one_query_per_work(client: TestClient, db: Session) -> None:
    from sqlalchemy import event

    from app.core.database import engine

    category = make_category(db)
    for i in range(10):
        make_work(db, category, title=f"Obra {i}", with_image=True, work_type=WorkType.VISUAL)
    statements: list[str] = []

    def record(conn, cursor, statement, *args):  # type: ignore[no-untyped-def]
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        assert len(client.get(WORKS).json()["items"]) == 10
    finally:
        event.remove(engine, "before_cursor_execute", record)
    assert len(statements) <= 4  # contagem + obras/categorias + mídias (+ folga)
