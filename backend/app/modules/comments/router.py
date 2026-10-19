from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, Response, status

from app.api.deps import CurrentAdmin, DbSession, get_current_admin
from app.core.config import get_settings
from app.core.pagination import PaginationDep
from app.core.rate_limit import limiter
from app.core.schemas import Page
from app.modules.comments import service
from app.modules.comments.models import CommentStatus
from app.modules.comments.schemas import CommentAdmin, CommentCreate, CommentReceived
from app.modules.moderation.models import ModerationAction
from app.modules.moderation.schemas import OptionalRejectionRequest

public_router = APIRouter(prefix="/works/{work_id}/comments", tags=["comments"])
admin_router = APIRouter(
    prefix="/admin/comments",
    tags=["admin: comments"],
    dependencies=[Depends(get_current_admin)],
)


@public_router.post("", response_model=CommentReceived, status_code=status.HTTP_201_CREATED)
@limiter.limit(lambda: get_settings().rate_limit_submit_comment)
def submit_comment(
    request: Request, work_id: int, payload: CommentCreate, db: DbSession
) -> CommentReceived:
    comment = service.submit_comment(db, work_id, payload)
    return CommentReceived(id=comment.id, status=comment.status)


@admin_router.get("", response_model=Page[CommentAdmin])
def admin_list_comments(
    db: DbSession,
    pagination: PaginationDep,
    status: CommentStatus | None = None,
    work_id: int | None = None,
    order: service.SortOrder = "newest",
) -> Page[CommentAdmin]:
    comments, total = service.list_admin_comments(
        db, pagination, status=status, work_id=work_id, order=order
    )
    return Page(
        items=[CommentAdmin.model_validate(c) for c in comments],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@admin_router.post("/{comment_id}/approve", response_model=CommentAdmin)
def approve_comment(comment_id: int, db: DbSession, admin: CurrentAdmin) -> CommentAdmin:
    comment = service.apply_action(db, admin, comment_id, ModerationAction.APPROVE)
    return CommentAdmin.model_validate(comment)


@admin_router.post("/{comment_id}/reject", response_model=CommentAdmin)
def reject_comment(
    comment_id: int,
    db: DbSession,
    admin: CurrentAdmin,
    payload: Annotated[OptionalRejectionRequest | None, Body()] = None,
) -> CommentAdmin:
    reason = payload.reason if payload else None
    comment = service.apply_action(db, admin, comment_id, ModerationAction.REJECT, reason)
    return CommentAdmin.model_validate(comment)


@admin_router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: DbSession, admin: CurrentAdmin) -> Response:
    service.delete_comment(db, admin, comment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
