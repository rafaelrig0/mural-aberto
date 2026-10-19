from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_current_admin
from app.core.pagination import PaginationDep
from app.core.schemas import Page
from app.modules.moderation import service
from app.modules.moderation.models import ModerationAction, ModerationTarget
from app.modules.moderation.schemas import ModerationLogRead

admin_router = APIRouter(
    prefix="/admin/moderation-logs",
    tags=["admin: moderation"],
    dependencies=[Depends(get_current_admin)],
)


@admin_router.get("", response_model=Page[ModerationLogRead])
def list_moderation_logs(
    db: DbSession,
    pagination: PaginationDep,
    target_type: ModerationTarget | None = None,
    target_id: int | None = None,
    admin_id: int | None = None,
    action: ModerationAction | None = None,
) -> Page[ModerationLogRead]:
    items, total = service.list_logs(
        db,
        pagination,
        target_type=target_type,
        target_id=target_id,
        admin_id=admin_id,
        action=action,
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
