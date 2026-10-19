"""Utilitários compartilhados pelos testes."""

from datetime import UTC, date, datetime
from io import BytesIO
from typing import Any

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.modules.categories.models import Category
from app.modules.comments.models import Comment, CommentStatus
from app.modules.media.models import MediaKind, WorkMedia
from app.modules.media.storage import StorageService
from app.modules.works.models import Work, WorkStatus, WorkType

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "senha-super-segura-123"  # noqa: S105

MP4_BYTES = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + b"\x00" * 64
EXECUTABLE_BYTES = b"MZ\x90\x00" + b"\x00" * 200


class FakeStorage(StorageService):
    """Storage em memória: nenhum teste fala com o Supabase de verdade."""

    def __init__(self) -> None:  # não chama super().__init__: não há cliente HTTP
        self.files: dict[str, bytes] = {}
        self.fail_uploads = False

    def upload(self, path: str, content: bytes, mime_type: str) -> None:
        if self.fail_uploads:
            from app.core.exceptions import StorageError

            raise StorageError
        self.files[path] = content

    def delete(self, paths: Any) -> None:
        for path in paths:
            self.files.pop(path, None)

    def create_signed_urls(self, paths: Any, expires_in: int) -> dict[str, str]:
        return {path: f"https://signed.example/{path}?token=t" for path in paths}


def image_bytes(fmt: str = "PNG") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (12, 12), "red").save(buffer, format=fmt)
    return buffer.getvalue()


def make_category(db: Session, name: str = "Fotografia") -> Category:
    category = Category(name=name, slug=name.lower())
    db.add(category)
    db.commit()
    return category


def make_work(  # noqa: PLR0913
    db: Session,
    category: Category,
    *,
    status: WorkStatus = WorkStatus.APPROVED,
    work_type: WorkType = WorkType.TEXT,
    title: str = "Poema da tarde",
    author_name: str = "Maria",
    with_image: bool = False,
) -> Work:
    now = datetime.now(UTC)
    work = Work(
        title=title,
        author_name=author_name,
        contact_email="maria@privado.com",
        category_id=category.id,
        work_type=work_type,
        created_on=date(2024, 5, 1),
        body_text="Versos em prosa." if work_type is WorkType.TEXT else None,
        alt_text="Descrição" if with_image else None,
        usage_authorized_at=now,
        status=status,
        approved_at=now if status in (WorkStatus.APPROVED, WorkStatus.ARCHIVED) else None,
        rejection_reason="Fora das regras" if status is WorkStatus.REJECTED else None,
    )
    if with_image:
        work.media.append(
            WorkMedia(
                kind=MediaKind.IMAGE,
                storage_path=f"works/seed-{title}.png",
                mime_type="image/png",
                size_bytes=10,
            )
        )
    db.add(work)
    db.commit()
    return work


def make_comment(
    db: Session, work: Work, status: CommentStatus = CommentStatus.PENDING, content: str = "Lindo!"
) -> Comment:
    comment = Comment(work_id=work.id, author_name="Joana", content=content, status=status)
    db.add(comment)
    db.commit()
    return comment


def text_work_form(category_id: int, **overrides: str) -> dict[str, str]:
    form = {
        "title": "Meu poema",
        "author_name": "Ana",
        "contact_email": "ana@example.com",
        "category_id": str(category_id),
        "work_type": "text",
        "created_on": "2024-03-10",
        "usage_authorized": "true",
        "body_text": "Era uma vez um verso.",
    }
    form.update(overrides)
    return form


def visual_work_form(category_id: int, **overrides: str) -> dict[str, str]:
    form = text_work_form(category_id, work_type="visual", alt_text="Um quadro vermelho")
    form.pop("body_text")
    form.update(overrides)
    return form


def post_work(
    client: TestClient, form: dict[str, str], files: dict[str, tuple[str, bytes, str]] | None = None
) -> Any:
    return client.post("/api/v1/works", data=form, files=files or None)
