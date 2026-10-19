from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.media.models import WorkMedia
from app.modules.works.models import Work, WorkStatus
from tests.helpers import (
    EXECUTABLE_BYTES,
    MP4_BYTES,
    FakeStorage,
    image_bytes,
    make_category,
    post_work,
    text_work_form,
    visual_work_form,
)


def count(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


def test_text_work_starts_pending_and_stores_consent(client: TestClient, db: Session) -> None:
    category = make_category(db)
    response = post_work(client, text_work_form(category.id))
    assert response.status_code == 201
    assert response.json() == {"id": 1, "status": "pending"}
    work = db.get(Work, 1)
    assert work is not None
    assert work.status is WorkStatus.PENDING
    assert work.usage_authorized_at is not None
    assert work.contact_email == "ana@example.com"


def test_visual_work_with_image_and_video(
    client: TestClient, db: Session, storage: FakeStorage
) -> None:
    category = make_category(db)
    files = {
        "image": ("minha foto.PNG", image_bytes("PNG"), "image/png"),
        "video": ("clipe.mp4", MP4_BYTES, "video/mp4"),
    }
    response = post_work(client, visual_work_form(category.id), files)
    assert response.status_code == 201
    media = db.scalars(select(WorkMedia).order_by(WorkMedia.kind)).all()
    assert sorted(m.mime_type for m in media) == ["image/png", "video/mp4"]
    assert len(storage.files) == 2
    # o nome enviado pelo usuário nunca vai para o storage
    assert all("minha" not in path and path.startswith("works/") for path in storage.files)


def test_blank_optional_fields_are_accepted(client: TestClient, db: Session) -> None:
    category = make_category(db)
    form = text_work_form(category.id, neighborhood="", alt_text="")
    assert post_work(client, form).status_code == 201
    assert db.get(Work, 1).neighborhood is None  # type: ignore[union-attr]


def test_requires_usage_authorization(client: TestClient, db: Session) -> None:
    category = make_category(db)
    response = post_work(client, text_work_form(category.id, usage_authorized="false"))
    assert response.status_code == 422
    assert count(db, Work) == 0


def test_text_work_requires_body_and_rejects_files(client: TestClient, db: Session) -> None:
    category = make_category(db)
    form = text_work_form(category.id)
    del form["body_text"]
    assert post_work(client, form).status_code == 422
    with_file = post_work(
        client, text_work_form(category.id), {"image": ("a.png", image_bytes(), "image/png")}
    )
    assert with_file.status_code == 422
    assert count(db, Work) == 0


def test_visual_work_requires_a_file_and_alt_text_for_image(
    client: TestClient, db: Session
) -> None:
    category = make_category(db)
    assert post_work(client, visual_work_form(category.id)).status_code == 422
    no_alt = post_work(
        client,
        visual_work_form(category.id, alt_text=""),
        {"image": ("a.png", image_bytes(), "image/png")},
    )
    assert no_alt.status_code == 422
    video_only = post_work(
        client,
        visual_work_form(category.id, alt_text=""),
        {"video": ("a.mp4", MP4_BYTES, "video/mp4")},
    )
    assert video_only.status_code == 201


def test_unknown_category_is_422(client: TestClient) -> None:
    assert post_work(client, text_work_form(999)).status_code == 422


def test_disguised_executable_is_rejected_and_nothing_is_saved(
    client: TestClient, db: Session, storage: FakeStorage
) -> None:
    category = make_category(db)
    response = post_work(
        client,
        visual_work_form(category.id),
        {"image": ("foto.png", EXECUTABLE_BYTES, "image/png")},
    )
    assert response.status_code == 415
    assert count(db, Work) == 0
    assert storage.files == {}


def test_oversized_image_is_413(client: TestClient, db: Session) -> None:
    category = make_category(db)
    big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (1024 * 1024 + 1)  # limite de teste: 1 MB
    response = post_work(
        client, visual_work_form(category.id), {"image": ("a.png", big, "image/png")}
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_total_body_over_limit_is_rejected_before_parsing(client: TestClient, db: Session) -> None:
    category = make_category(db)
    huge = b"\x00" * (5 * 1024 * 1024)  # limite do corpo no teste: 1 + 2 + 1 MB = 4 MB
    response = post_work(
        client, visual_work_form(category.id), {"image": ("a.png", huge, "image/png")}
    )
    assert response.status_code == 413


def test_chunked_body_over_limit_is_rejected(client: TestClient) -> None:
    def chunks():  # type: ignore[no-untyped-def]
        for _ in range(6):
            yield b"\x00" * (1024 * 1024)

    response = client.post(
        "/api/v1/works",
        content=chunks(),
        headers={"Content-Type": "multipart/form-data; boundary=x"},
    )
    assert response.status_code == 413


def test_other_endpoints_have_small_default_body_limit(client: TestClient) -> None:
    response = client.post("/api/v1/auth/login", content=b"x" * (2 * 1024 * 1024))
    assert response.status_code == 413


def test_storage_failure_saves_nothing(
    client: TestClient, db: Session, storage: FakeStorage
) -> None:
    category = make_category(db)
    storage.fail_uploads = True
    response = post_work(
        client, visual_work_form(category.id), {"image": ("a.png", image_bytes(), "image/png")}
    )
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "storage_unavailable"
    assert count(db, Work) == 0


def test_database_failure_after_upload_removes_uploaded_files(
    client: TestClient, db: Session, storage: FakeStorage, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    category = make_category(db)

    def broken_commit(self: Session) -> None:
        raise RuntimeError("falha simulada do banco")

    monkeypatch.setattr(Session, "commit", broken_commit)
    response = post_work(
        client, visual_work_form(category.id), {"image": ("a.png", image_bytes(), "image/png")}
    )
    monkeypatch.undo()
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Erro interno do servidor."}
    }
    assert storage.files == {}  # compensação: nenhum arquivo órfão
    assert count(db, Work) == 0


def test_submission_is_rate_limited(client: TestClient, db: Session) -> None:
    from app.core.rate_limit import limiter

    category = make_category(db)
    limiter.enabled = True
    limiter.reset()
    try:
        codes = [post_work(client, text_work_form(category.id)).status_code for _ in range(11)]
    finally:
        limiter.enabled = False
    assert codes[:10] == [201] * 10
    assert codes[10] == 429
