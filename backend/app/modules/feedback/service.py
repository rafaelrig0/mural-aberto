import logging
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.pagination import Pagination
from app.modules.feedback.models import Feedback, FeedbackType
from app.modules.feedback.schemas import FeedbackCreate

logger = logging.getLogger(__name__)

SortOrder = Literal["newest", "oldest"]


def submit_feedback(db: Session, payload: FeedbackCreate) -> Feedback:
    feedback = Feedback(
        author_name=payload.author_name,
        feedback_type=payload.feedback_type,
        message=payload.message,
        rating=payload.rating,
    )
    db.add(feedback)
    db.commit()
    logger.info("Feedback %s recebido (tipo=%s)", feedback.id, feedback.feedback_type.value)
    return feedback


def list_admin_feedback(
    db: Session,
    pagination: Pagination,
    *,
    feedback_type: FeedbackType | None,
    order: SortOrder,
) -> tuple[list[Feedback], int]:
    filters = []
    if feedback_type is not None:
        filters.append(Feedback.feedback_type == feedback_type)

    total = db.scalar(select(func.count()).select_from(Feedback).where(*filters)) or 0
    ordering = (
        (Feedback.created_at.asc(), Feedback.id.asc())
        if order == "oldest"
        else (Feedback.created_at.desc(), Feedback.id.desc())
    )
    items = db.scalars(
        select(Feedback)
        .where(*filters)
        .order_by(*ordering)
        .limit(pagination.page_size)
        .offset(pagination.offset)
    ).all()
    return list(items), total
