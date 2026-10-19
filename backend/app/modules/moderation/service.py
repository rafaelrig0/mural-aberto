from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.pagination import Pagination
from app.modules.admins.models import Admin
from app.modules.moderation.models import ModerationAction, ModerationLog, ModerationTarget
from app.modules.moderation.schemas import ModerationLogRead


def record_action(
    db: Session,
    *,
    admin_id: int,
    target_type: ModerationTarget,
    target_id: int,
    action: ModerationAction,
    reason: str | None = None,
) -> ModerationLog:
    """Adiciona o log à sessão SEM commit: quem chama confirma junto com a mudança de estado,
    garantindo que estado e registro de auditoria sejam gravados juntos (ou nenhum dos dois)."""
    log = ModerationLog(
        admin_id=admin_id,
        target_type=target_type,
        target_id=target_id,
        action=action,
        reason=reason,
    )
    db.add(log)
    return log


def list_logs(
    db: Session,
    pagination: Pagination,
    *,
    target_type: ModerationTarget | None = None,
    target_id: int | None = None,
    admin_id: int | None = None,
    action: ModerationAction | None = None,
) -> tuple[list[ModerationLogRead], int]:
    filters = []
    if target_type is not None:
        filters.append(ModerationLog.target_type == target_type)
    if target_id is not None:
        filters.append(ModerationLog.target_id == target_id)
    if admin_id is not None:
        filters.append(ModerationLog.admin_id == admin_id)
    if action is not None:
        filters.append(ModerationLog.action == action)

    total = db.scalar(select(func.count()).select_from(ModerationLog).where(*filters)) or 0
    rows = db.execute(
        select(ModerationLog, Admin.email)
        .join(Admin, Admin.id == ModerationLog.admin_id)
        .where(*filters)
        .order_by(ModerationLog.created_at.desc(), ModerationLog.id.desc())
        .limit(pagination.page_size)
        .offset(pagination.offset)
    ).all()
    items = [
        ModerationLogRead(
            id=log.id,
            admin_id=log.admin_id,
            admin_email=email,
            target_type=log.target_type,
            target_id=log.target_id,
            action=log.action,
            reason=log.reason,
            created_at=log.created_at,
        )
        for log, email in rows
    ]
    return items, total
