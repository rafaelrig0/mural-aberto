from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api.deps import CurrentAdmin, DbSession, get_current_admin
from app.core.config import get_settings
from app.core.pagination import PaginationDep
from app.core.rate_limit import limiter
from app.core.schemas import Page
from app.modules.media.storage import StorageDep
from app.modules.moderation.models import ModerationAction
from app.modules.moderation.schemas import RejectionRequest
from app.modules.works import moderation_service, presenters, service
from app.modules.works.models import WorkStatus, WorkType
from app.modules.works.schemas import (
    WorkAdmin,
    WorkPublicDetail,
    WorkPublicSummary,
    WorkReceived,
    WorkSubmission,
)

public_router = APIRouter(prefix="/works", tags=["works"])
admin_router = APIRouter(
    prefix="/admin/works",
    tags=["admin: works"],
    dependencies=[Depends(get_current_admin)],
)


# ------------------------------------------------------------------ público


@public_router.get("", response_model=Page[WorkPublicSummary])
def list_works(
    db: DbSession,
    storage: StorageDep,
    pagination: PaginationDep,
    category_id: int | None = None,
    work_type: WorkType | None = None,
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
) -> Page[WorkPublicSummary]:
    filters = service.CatalogFilters(category_id=category_id, work_type=work_type, query=q)
    works, total = service.list_public_works(db, filters, pagination)
    urls = service.sign_media_urls(storage, works)
    return Page(
        items=[presenters.to_public_summary(w, urls) for w in works],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@public_router.get("/{work_id}", response_model=WorkPublicDetail)
def get_work(work_id: int, db: DbSession, storage: StorageDep) -> WorkPublicDetail:
    work, comments = service.get_public_work(db, work_id)
    urls = service.sign_media_urls(storage, [work])
    return presenters.to_public_detail(work, comments, urls)


@public_router.post("", response_model=WorkReceived, status_code=status.HTTP_201_CREATED)
@limiter.limit(lambda: get_settings().rate_limit_submit_work)
def submit_work(  # noqa: PLR0913  (um parâmetro por campo do formulário multipart)
    request: Request,
    db: DbSession,
    storage: StorageDep,
    title: Annotated[str, Form()],
    author_name: Annotated[str, Form()],
    contact_email: Annotated[str, Form()],
    category_id: Annotated[int, Form()],
    work_type: Annotated[WorkType, Form()],
    created_on: Annotated[date, Form()],
    usage_authorized: Annotated[bool, Form()],
    neighborhood: Annotated[str | None, Form()] = None,
    body_text: Annotated[str | None, Form()] = None,
    alt_text: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
    video: Annotated[UploadFile | None, File()] = None,
) -> WorkReceived:
    try:
        submission = WorkSubmission(
            title=title,
            author_name=author_name,
            contact_email=contact_email,
            category_id=category_id,
            work_type=work_type,
            created_on=created_on,
            neighborhood=neighborhood,
            body_text=body_text,
            alt_text=alt_text,
            usage_authorized=usage_authorized,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc
    work = service.submit_work(db, storage, submission, image, video)
    return WorkReceived(id=work.id, status=work.status)


# ------------------------------------------------------------------ administração


@admin_router.get("", response_model=Page[WorkAdmin])
def admin_list_works(
    db: DbSession,
    storage: StorageDep,
    pagination: PaginationDep,
    status: WorkStatus | None = None,
    order: service.SortOrder = "newest",
) -> Page[WorkAdmin]:
    works, total = service.list_admin_works(db, pagination, status, order)
    urls = service.sign_media_urls(storage, works)
    return Page(
        items=[presenters.to_admin(w, urls) for w in works],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@admin_router.get("/{work_id}", response_model=WorkAdmin)
def admin_get_work(work_id: int, db: DbSession, storage: StorageDep) -> WorkAdmin:
    work = service.get_admin_work(db, work_id)
    return presenters.to_admin(work, service.sign_media_urls(storage, [work]))


def _moderate(
    db: DbSession,
    storage: StorageDep,
    admin: CurrentAdmin,
    work_id: int,
    action: ModerationAction,
    reason: str | None = None,
) -> WorkAdmin:
    work = moderation_service.apply_action(db, admin, work_id, action, reason)
    return presenters.to_admin(work, service.sign_media_urls(storage, [work]))


@admin_router.post("/{work_id}/approve", response_model=WorkAdmin)
def approve_work(
    work_id: int, db: DbSession, storage: StorageDep, admin: CurrentAdmin
) -> WorkAdmin:
    return _moderate(db, storage, admin, work_id, ModerationAction.APPROVE)


@admin_router.post("/{work_id}/reject", response_model=WorkAdmin)
def reject_work(
    work_id: int,
    payload: RejectionRequest,
    db: DbSession,
    storage: StorageDep,
    admin: CurrentAdmin,
) -> WorkAdmin:
    return _moderate(db, storage, admin, work_id, ModerationAction.REJECT, payload.reason)


@admin_router.post("/{work_id}/archive", response_model=WorkAdmin)
def archive_work(
    work_id: int, db: DbSession, storage: StorageDep, admin: CurrentAdmin
) -> WorkAdmin:
    return _moderate(db, storage, admin, work_id, ModerationAction.ARCHIVE)


@admin_router.post("/{work_id}/unarchive", response_model=WorkAdmin)
def unarchive_work(
    work_id: int, db: DbSession, storage: StorageDep, admin: CurrentAdmin
) -> WorkAdmin:
    return _moderate(db, storage, admin, work_id, ModerationAction.UNARCHIVE)


@admin_router.delete("/{work_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work(work_id: int, db: DbSession, storage: StorageDep, admin: CurrentAdmin) -> Response:
    moderation_service.delete_work(db, storage, admin, work_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
