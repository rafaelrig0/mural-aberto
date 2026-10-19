from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.comments.models import Comment
from app.modules.media.models import WorkMedia
from app.modules.moderation.models import ModerationAction, ModerationLog, ModerationTarget
from app.modules.works.models import Work, WorkStatus, WorkType
from tests.helpers import FakeStorage, make_category, make_comment, make_work

ADMIN = "/api/v1/admin/works"


def logs(db: Session) -> list[ModerationLog]:
    return list(db.scalars(select(ModerationLog).order_by(ModerationLog.id)))


def test_all_admin_work_endpoints_require_auth(client: TestClient, db: Session) -> None:
    work = make_work(db, make_category(db), status=WorkStatus.PENDING)
    url = f"{ADMIN}/{work.id}"
    calls = [
        client.get(ADMIN),
        client.get(url),
        client.post(f"{url}/approve"),
        client.post(f"{url}/reject", json={"reason": "motivo"}),
        client.post(f"{url}/archive"),
        client.post(f"{url}/unarchive"),
        client.delete(url),
    ]
    assert [c.status_code for c in calls] == [401] * 7
    db.refresh(work)
    assert work.status is WorkStatus.PENDING
    assert logs(db) == []


def test_admin_list_shows_all_statuses_and_private_data(
    client: TestClient, auth: dict[str, str], db: Session
) -> None:
    category = make_category(db)
    make_work(db, category, status=WorkStatus.PENDING, title="P")
    make_work(db, category, status=WorkStatus.REJECTED, title="R")
    everything = client.get(ADMIN, headers=auth).json()
    assert everything["total"] == 2
    assert everything["items"][0]["contact_email"] == "maria@privado.com"
    pending = client.get(ADMIN, params={"status": "pending", "order": "oldest"}, headers=auth)
    assert [w["title"] for w in pending.json()["items"]] == ["P"]


def test_approve_makes_work_public_and_writes_audit_log(
    client: TestClient, auth: dict[str, str], db: Session, admin
) -> None:  # type: ignore[no-untyped-def]
    work = make_work(db, make_category(db), status=WorkStatus.PENDING)
    assert client.get(f"/api/v1/works/{work.id}").status_code == 404

    response = client.post(f"{ADMIN}/{work.id}/approve", headers=auth)
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["approved_at"] is not None
    assert client.get(f"/api/v1/works/{work.id}").status_code == 200

    (log,) = logs(db)
    assert (log.admin_id, log.target_type, log.target_id, log.action) == (
        admin.id,
        ModerationTarget.WORK,
        work.id,
        ModerationAction.APPROVE,
    )


def test_reject_requires_reason_and_records_it(
    client: TestClient, auth: dict[str, str], db: Session
) -> None:
    work = make_work(db, make_category(db), status=WorkStatus.PENDING)
    assert client.post(f"{ADMIN}/{work.id}/reject", headers=auth).status_code == 422
    assert (
        client.post(f"{ADMIN}/{work.id}/reject", json={"reason": " "}, headers=auth).status_code
        == 422
    )
    response = client.post(
        f"{ADMIN}/{work.id}/reject", json={"reason": "Conteúdo ofensivo"}, headers=auth
    )
    assert response.status_code == 200
    assert response.json()["rejection_reason"] == "Conteúdo ofensivo"
    assert [log.reason for log in logs(db)] == ["Conteúdo ofensivo"]
    assert client.get(f"/api/v1/works/{work.id}").status_code == 404


def test_rejected_is_final(client: TestClient, auth: dict[str, str], db: Session) -> None:
    work = make_work(db, make_category(db), status=WorkStatus.REJECTED)
    for action, body in (("approve", None), ("archive", None), ("unarchive", None)):
        response = client.post(f"{ADMIN}/{work.id}/{action}", headers=auth, json=body)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "invalid_transition"
    assert logs(db) == []  # transição inválida não gera log


def test_archive_and_unarchive_cycle(client: TestClient, auth: dict[str, str], db: Session) -> None:
    work = make_work(db, make_category(db))
    archived = client.post(f"{ADMIN}/{work.id}/archive", headers=auth).json()
    assert archived["status"] == "archived"
    assert archived["archived_at"] is not None
    assert client.get(f"/api/v1/works/{work.id}").status_code == 404

    restored = client.post(f"{ADMIN}/{work.id}/unarchive", headers=auth).json()
    assert restored["status"] == "approved"
    assert restored["archived_at"] is None
    assert client.get(f"/api/v1/works/{work.id}").status_code == 200
    assert [log.action for log in logs(db)] == [
        ModerationAction.ARCHIVE,
        ModerationAction.UNARCHIVE,
    ]


def test_double_approve_conflicts(client: TestClient, auth: dict[str, str], db: Session) -> None:
    work = make_work(db, make_category(db), status=WorkStatus.PENDING)
    assert client.post(f"{ADMIN}/{work.id}/approve", headers=auth).status_code == 200
    assert client.post(f"{ADMIN}/{work.id}/approve", headers=auth).status_code == 409
    assert len(logs(db)) == 1


def test_moderating_missing_work_is_404(client: TestClient, auth: dict[str, str]) -> None:
    assert client.post(f"{ADMIN}/999/approve", headers=auth).status_code == 404
    assert client.get(f"{ADMIN}/999", headers=auth).status_code == 404
    assert client.delete(f"{ADMIN}/999", headers=auth).status_code == 404


def test_delete_removes_files_comments_and_keeps_anonymous_log(
    client: TestClient, auth: dict[str, str], db: Session, storage: FakeStorage
) -> None:
    work = make_work(db, make_category(db), work_type=WorkType.VISUAL, with_image=True)
    make_comment(db, work)
    work_id = work.id
    storage.files[work.media[0].storage_path] = b"bytes"

    assert client.delete(f"{ADMIN}/{work_id}", headers=auth).status_code == 204

    db.expire_all()
    assert db.get(Work, work_id) is None
    assert db.scalar(select(func.count()).select_from(WorkMedia)) == 0
    assert db.scalar(select(func.count()).select_from(Comment)) == 0
    assert storage.files == {}
    (log,) = logs(db)
    assert (log.target_id, log.action, log.reason) == (work_id, ModerationAction.DELETE, None)


def test_audit_log_endpoint_lists_and_filters(
    client: TestClient, auth: dict[str, str], db: Session
) -> None:
    category = make_category(db)
    first = make_work(db, category, status=WorkStatus.PENDING)
    second = make_work(db, category, status=WorkStatus.PENDING)
    client.post(f"{ADMIN}/{first.id}/approve", headers=auth)
    client.post(f"{ADMIN}/{second.id}/reject", json={"reason": "Fora do tema"}, headers=auth)

    url = "/api/v1/admin/moderation-logs"
    everything = client.get(url, headers=auth).json()
    assert everything["total"] == 2
    assert everything["items"][0]["action"] == "reject"  # mais recente primeiro
    assert everything["items"][0]["admin_email"] == "admin@example.com"
    only_rejects = client.get(url, params={"action": "reject"}, headers=auth).json()
    assert only_rejects["total"] == 1
    by_target = client.get(url, params={"target_type": "work", "target_id": first.id}, headers=auth)
    assert by_target.json()["items"][0]["action"] == "approve"
    assert client.get(url).status_code == 401


def test_race_between_two_moderators_only_one_wins(db: Session, admin) -> None:  # type: ignore[no-untyped-def]
    """Duas ações simultâneas na mesma obra: a trava de linha serializa, a segunda falha."""
    import threading

    from app.core.database import SessionLocal
    from app.core.exceptions import InvalidTransitionError
    from app.modules.works import moderation_service

    work = make_work(db, make_category(db), status=WorkStatus.PENDING)
    outcomes: list[str] = []
    barrier = threading.Barrier(2)

    def moderate(action: ModerationAction) -> None:
        with SessionLocal() as session:
            barrier.wait()
            try:
                moderation_service.apply_action(session, admin, work.id, action, "motivo")
                outcomes.append("ok")
            except InvalidTransitionError:
                outcomes.append("conflict")

    threads = [
        threading.Thread(target=moderate, args=(ModerationAction.APPROVE,)),
        threading.Thread(target=moderate, args=(ModerationAction.REJECT,)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(outcomes) == ["conflict", "ok"]
    assert len(logs(db)) == 1
