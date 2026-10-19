import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from fastapi import UploadFile
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, StorageError, UnprocessableError
from app.core.pagination import Pagination
from app.modules.categories.models import Category
from app.modules.comments.models import Comment, CommentStatus
from app.modules.media.models import WorkMedia
from app.modules.media.storage import StorageService, new_storage_path
from app.modules.media.validation import ValidatedFile, validate_image, validate_video
from app.modules.works.models import Work, WorkStatus, WorkType
from app.modules.works.presenters import storage_paths
from app.modules.works.schemas import WorkSubmission

logger = logging.getLogger(__name__)

SortOrder = Literal["newest", "oldest"]


@dataclass(frozen=True)
class CatalogFilters:
    category_id: int | None = None
    work_type: WorkType | None = None
    query: str | None = None


def _with_relations(stmt: Select[Work]) -> Select[Work]:
    """Carrega categoria e mídias junto com as obras (evita o problema de N+1)."""
    return stmt.options(joinedload(Work.category), selectinload(Work.media))


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def sign_media_urls(storage: StorageService, works: list[Work]) -> dict[str, str]:
    """URLs assinadas em lote. Se o storage falhar, a listagem continua, só sem as mídias."""
    paths = storage_paths(works)
    try:
        return storage.create_signed_urls(paths, get_settings().signed_url_expire_seconds)
    except StorageError:
        return {}


# ---------------------------------------------------------------- envio público


def _as_upload(upload: UploadFile | None) -> UploadFile | None:
    """Campo de arquivo deixado em branco no formulário chega com nome vazio: não é um envio."""
    return upload if upload is not None and upload.filename else None


def _validate_files(
    submission: WorkSubmission, image: UploadFile | None, video: UploadFile | None
) -> list[ValidatedFile]:
    if submission.work_type is WorkType.TEXT:
        if image or video:
            raise UnprocessableError("Obras textuais não aceitam arquivos de imagem ou vídeo.")
        return []
    if not image and not video:
        raise UnprocessableError("Obras visuais exigem uma imagem ou um vídeo.")
    if image and not submission.alt_text:
        raise UnprocessableError("Informe o texto alternativo (acessibilidade) da imagem.")

    settings = get_settings()
    files: list[ValidatedFile] = []
    if image:
        files.append(validate_image(image, settings.max_image_size_bytes))
    if video:
        files.append(validate_video(video, settings.max_video_size_bytes))
    return files


def submit_work(
    db: Session,
    storage: StorageService,
    submission: WorkSubmission,
    image: UploadFile | None,
    video: UploadFile | None,
) -> Work:
    """Valida tudo antes de gravar qualquer coisa; só então sobe os arquivos e grava no banco.

    Upload e banco não compartilham transação: se o banco falhar depois do upload, os
    arquivos já enviados são apagados (compensação)."""
    files = _validate_files(submission, _as_upload(image), _as_upload(video))

    if db.get(Category, submission.category_id) is None:
        raise UnprocessableError("Categoria inexistente.")
    db.rollback()  # libera a conexão do pool antes dos uploads, que podem ser lentos

    work = Work(
        title=submission.title,
        author_name=submission.author_name,
        contact_email=submission.contact_email,
        category_id=submission.category_id,
        work_type=submission.work_type,
        created_on=submission.created_on,
        neighborhood=submission.neighborhood,
        body_text=submission.body_text,
        alt_text=submission.alt_text,
        usage_authorized_at=datetime.now(UTC),
    )
    uploaded_paths: list[str] = []
    try:
        for file in files:
            path = new_storage_path(file.extension)
            uploaded_paths.append(path)  # registrado antes: se o upload falhar, tenta limpar
            storage.upload(path, file.content, file.mime_type)
            work.media.append(
                WorkMedia(
                    kind=file.kind,
                    storage_path=path,
                    mime_type=file.mime_type,
                    size_bytes=len(file.content),
                )
            )
        db.add(work)
        db.commit()
    except Exception:
        db.rollback()
        storage.delete_quietly(uploaded_paths)
        raise
    logger.info("Obra %s recebida (tipo=%s)", work.id, work.work_type.value)
    return work


# ---------------------------------------------------------------- catálogo público


def list_public_works(
    db: Session, filters: CatalogFilters, pagination: Pagination
) -> tuple[list[Work], int]:
    stmt = select(Work).where(Work.status == WorkStatus.APPROVED)
    if filters.category_id is not None:
        stmt = stmt.where(Work.category_id == filters.category_id)
    if filters.work_type is not None:
        stmt = stmt.where(Work.work_type == filters.work_type)
    if filters.query:
        pattern = f"%{_escape_like(filters.query)}%"
        stmt = stmt.where(
            Work.title.ilike(pattern, escape="\\") | Work.author_name.ilike(pattern, escape="\\")
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    works = db.scalars(
        _with_relations(stmt)
        .order_by(Work.approved_at.desc(), Work.id.desc())
        .limit(pagination.page_size)
        .offset(pagination.offset)
    ).all()
    return list(works), total


def get_public_work(db: Session, work_id: int) -> tuple[Work, list[Comment]]:
    """Obra não aprovada responde como inexistente: não revela que existe."""
    work = db.scalar(
        _with_relations(select(Work).where(Work.id == work_id, Work.status == WorkStatus.APPROVED))
    )
    if work is None:
        raise NotFoundError("Obra não encontrada.")
    comments = db.scalars(
        select(Comment)
        .where(Comment.work_id == work_id, Comment.status == CommentStatus.APPROVED)
        .order_by(Comment.created_at, Comment.id)
    ).all()
    return work, list(comments)


# ---------------------------------------------------------------- consulta administrativa


def list_admin_works(
    db: Session, pagination: Pagination, status: WorkStatus | None, order: SortOrder
) -> tuple[list[Work], int]:
    stmt = select(Work)
    if status is not None:
        stmt = stmt.where(Work.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    ordering = (
        (Work.created_at.asc(), Work.id.asc())
        if order == "oldest"
        else (
            Work.created_at.desc(),
            Work.id.desc(),
        )
    )
    works = db.scalars(
        _with_relations(stmt)
        .order_by(*ordering)
        .limit(pagination.page_size)
        .offset(pagination.offset)
    ).all()
    return list(works), total


def get_admin_work(db: Session, work_id: int) -> Work:
    work = db.scalar(_with_relations(select(Work).where(Work.id == work_id)))
    if work is None:
        raise NotFoundError("Obra não encontrada.")
    return work
