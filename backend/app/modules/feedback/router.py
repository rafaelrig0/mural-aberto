from fastapi import APIRouter, Depends, Request, status

from app.api.deps import DbSession, get_current_admin
from app.core.config import get_settings
from app.core.pagination import PaginationDep
from app.core.rate_limit import limiter
from app.core.schemas import Page
from app.modules.feedback import service
from app.modules.feedback.models import FeedbackType
from app.modules.feedback.schemas import FeedbackAdmin, FeedbackCreate, FeedbackReceived

public_router = APIRouter(prefix="/feedback", tags=["feedback"])
admin_router = APIRouter(
    prefix="/admin/feedback",
    tags=["admin: feedback"],
    dependencies=[Depends(get_current_admin)],
)


@public_router.post("", response_model=FeedbackReceived, status_code=status.HTTP_201_CREATED)
@limiter.limit(lambda: get_settings().rate_limit_submit_feedback)
def submit_feedback(request: Request, payload: FeedbackCreate, db: DbSession) -> FeedbackReceived:
    feedback = service.submit_feedback(db, payload)
    return FeedbackReceived(id=feedback.id)


@admin_router.get("", response_model=Page[FeedbackAdmin])
def admin_list_feedback(
    db: DbSession,
    pagination: PaginationDep,
    feedback_type: FeedbackType | None = None,
    order: service.SortOrder = "newest",
) -> Page[FeedbackAdmin]:
    items, total = service.list_admin_feedback(
        db, pagination, feedback_type=feedback_type, order=order
    )
    return Page(
        items=[FeedbackAdmin.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )
