from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.modules.comments.models import Comment, CommentStatus
from app.modules.moderation.models import ModerationLog
from app.modules.works.models import WorkStatus
from tests.helpers import make_category, make_comment, make_work

ADMIN = "/api/v1/admin/comments"


def comments_url(work_id: int) -> str:
    return f"/api/v1/works/{work_id}/comments"


def test_new_comment_is_pending_and_hidden(client: TestClient, db: Session) -> None:
    work = make_work(db, make_category(db))
    response = client.post(
        comments_url(work.id), json={"author_name": "  Zé ", "content": " Que bonito! "}
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    stored = db.scalars(select(Comment)).one()
    assert (stored.author_name, stored.content) == ("Zé", "Que bonito!")
    assert client.get(f"/api/v1/works/{work.id}").json()["comments"] == []


def test_cannot_comment_on_non_approved_or_missing_work(client: TestClient, db: Session) -> None:
    category = make_category(db)
    payload = {"author_name": "Zé", "content": "oi"}
    for status in (WorkStatus.PENDING, WorkStatus.REJECTED, WorkStatus.ARCHIVED):
        work = make_work(db, category, status=status)
        assert client.post(comments_url(work.id), json=payload).status_code == 404
    assert client.post(comments_url(9999), json=payload).status_code == 404


def test_comment_validation(client: TestClient, db: Session) -> None:
    work = make_work(db, make_category(db))
    url = comments_url(work.id)
    assert client.post(url, json={"author_name": "", "content": "x"}).status_code == 422
    assert client.post(url, json={"author_name": "Zé", "content": "  "}).status_code == 422
    assert client.post(url, json={"author_name": "Zé", "content": "x" * 2001}).status_code == 422
    assert client.post(url, json={"author_name": "Zé"}).status_code == 422


def test_moderation_flow(client: TestClient, auth: dict[str, str], db: Session) -> None:
    work = make_work(db, make_category(db))
    first, second = make_comment(db, work, content="bom"), make_comment(db, work, content="ruim")

    approved = client.post(f"{ADMIN}/{first.id}/approve", headers=auth)
    assert approved.json()["status"] == "approved"
    visible = client.get(f"/api/v1/works/{work.id}").json()["comments"]
    assert [c["content"] for c in visible] == ["bom"]

    rejected = client.post(f"{ADMIN}/{second.id}/reject", headers=auth)  # sem motivo: permitido
    assert rejected.status_code == 200
    assert rejected.json()["rejection_reason"] is None
    assert len(db.scalars(select(ModerationLog)).all()) == 2


def test_reject_with_reason(client: TestClient, auth: dict[str, str], db: Session) -> None:
    comment = make_comment(db, make_work(db, make_category(db)))
    response = client.post(f"{ADMIN}/{comment.id}/reject", json={"reason": "Spam"}, headers=auth)
    assert response.json()["rejection_reason"] == "Spam"


def test_comment_transitions_are_enforced(
    client: TestClient, auth: dict[str, str], db: Session
) -> None:
    work = make_work(db, make_category(db))
    approved = make_comment(db, work, CommentStatus.APPROVED)
    rejected = make_comment(db, work, CommentStatus.REJECTED)
    assert client.post(f"{ADMIN}/{approved.id}/approve", headers=auth).status_code == 409
    assert client.post(f"{ADMIN}/{approved.id}/reject", headers=auth).status_code == 409
    assert client.post(f"{ADMIN}/{rejected.id}/approve", headers=auth).status_code == 409
    assert client.post(f"{ADMIN}/9999/approve", headers=auth).status_code == 404


def test_admin_list_filters_and_delete(
    client: TestClient, auth: dict[str, str], db: Session
) -> None:
    work = make_work(db, make_category(db))
    pending = make_comment(db, work)
    make_comment(db, work, CommentStatus.APPROVED)

    only_pending = client.get(ADMIN, params={"status": "pending"}, headers=auth).json()
    assert [c["id"] for c in only_pending["items"]] == [pending.id]
    assert client.get(ADMIN, params={"work_id": work.id}, headers=auth).json()["total"] == 2

    assert client.delete(f"{ADMIN}/{pending.id}", headers=auth).status_code == 204
    assert client.get(ADMIN, headers=auth).json()["total"] == 1
    assert db.scalars(select(ModerationLog)).one().target_id == pending.id


def test_admin_comment_endpoints_require_auth(client: TestClient, db: Session) -> None:
    comment = make_comment(db, make_work(db, make_category(db)))
    url = f"{ADMIN}/{comment.id}"
    codes = [
        client.get(ADMIN).status_code,
        client.post(f"{url}/approve").status_code,
        client.post(f"{url}/reject").status_code,
        client.delete(url).status_code,
    ]
    assert codes == [401] * 4


def test_comment_submission_is_rate_limited(client: TestClient, db: Session) -> None:
    work = make_work(db, make_category(db))
    limiter.enabled = True
    limiter.reset()
    try:
        codes = [
            client.post(
                comments_url(work.id), json={"author_name": "Zé", "content": "oi"}
            ).status_code
            for _ in range(21)
        ]
    finally:
        limiter.enabled = False
    assert codes[:20] == [201] * 20
    assert codes[20] == 429


def test_blank_rejection_reason_is_stored_as_none(
    client: TestClient, auth: dict[str, str], db: Session
) -> None:
    comment = make_comment(db, make_work(db, make_category(db)))
    response = client.post(f"{ADMIN}/{comment.id}/reject", json={"reason": "   "}, headers=auth)
    assert response.status_code == 200
    assert response.json()["rejection_reason"] is None
