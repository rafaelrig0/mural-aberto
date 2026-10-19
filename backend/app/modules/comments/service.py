import logging
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.pagination import Pagination
from app.modules.admins.models import Admin
from app.modules.comments.models import Comment, CommentStatus
from app.modules.comments.schemas import CommentCreate
from app.modules.comments.state import next_status
from app.modules.moderation.models import ModerationAction, ModerationTarget
from app.modules.moderation.service import record_action
from app.modules.works.models import Work, WorkStatus

logger = logging.getLogger(__name__)

SortOrder = Literal["newest", "oldest"]


def submit_comment(db: Session, work_id: int, payload: CommentCreate) -> Comment:
    """Só obras aprovadas (visíveis ao público) aceitam comentários."""
    approved = db.scalar(
        select(Work.id).where(Work.id == work_id, Work.status == WorkStatus.APPROVED)
    )
    if approved is None:
        raise NotFoundError("Obra não encontrada.")
    comment = Comment(work_id=work_id, author_name=payload.author_name, content=payload.content)
    db.add(comment)
    db.commit()
    return comment


def list_admin_comments(
    db: Session,
    pagination: Pagination,
    *,
    status: CommentStatus | None,
    work_id: int | None,
    order: SortOrder,
) -> tuple[list[Comment], int]:
    filters = []
    if status is not None:
        filters.append(Comment.status == status)
    if work_id is not None:
        filters.append(Comment.work_id == work_id)

    total = db.scalar(select(func.count()).select_from(Comment).where(*filters)) or 0
    ordering = (
        (Comment.created_at.asc(), Comment.id.asc())
        if order == "oldest"
        else (Comment.created_at.desc(), Comment.id.desc())
    )
    comments = db.scalars(
        select(Comment)
        .where(*filters)
        .order_by(*ordering)
        .limit(pagination.page_size)
        .offset(pagination.offset)
    ).all()
    return list(comments), total


def _get_locked_comment(db: Session, comment_id: int) -> Comment:
    comment = db.scalar(select(Comment).where(Comment.id == comment_id).with_for_update())
    if comment is None:
        raise NotFoundError("Comentário não encontrado.")
    return comment


def apply_action(
    db: Session,
    admin: Admin,
    comment_id: int,
    action: ModerationAction,
    reason: str | None = None,
) -> Comment:
    comment = _get_locked_comment(db, comment_id)
    comment.status = next_status(action, comment.status)
    if action is ModerationAction.REJECT:
        comment.rejection_reason = reason
    record_action(
        db,
        admin_id=admin.id,
        target_type=ModerationTarget.COMMENT,
        target_id=comment.id,
        action=action,
        reason=reason,
    )
    db.commit()
    logger.info("Admin %s aplicou '%s' no comentário %s", admin.id, action.value, comment.id)
    return comment


def delete_comment(db: Session, admin: Admin, comment_id: int) -> None:
    comment = _get_locked_comment(db, comment_id)
    record_action(
        db,
        admin_id=admin.id,
        target_type=ModerationTarget.COMMENT,
        target_id=comment.id,
        action=ModerationAction.DELETE,
    )
    db.delete(comment)
    db.commit()
    logger.info("Admin %s excluiu o comentário %s", admin.id, comment_id)
