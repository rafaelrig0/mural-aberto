import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.exceptions import NotFoundError
from app.modules.admins.models import Admin
from app.modules.media.storage import StorageService
from app.modules.moderation.models import ModerationAction, ModerationTarget
from app.modules.moderation.service import record_action
from app.modules.works.models import Work
from app.modules.works.presenters import storage_paths
from app.modules.works.state import next_status

logger = logging.getLogger(__name__)


def _get_locked_work(db: Session, work_id: int) -> Work:
    """Trava a linha (SELECT ... FOR UPDATE): dois admins agindo na mesma obra ao mesmo tempo
    são serializados, e o segundo enxerga o estado já alterado pelo primeiro."""
    work = db.scalar(
        select(Work)
        .where(Work.id == work_id)
        .options(joinedload(Work.category), selectinload(Work.media))
        .with_for_update(of=Work)
    )
    if work is None:
        raise NotFoundError("Obra não encontrada.")
    return work


def apply_action(
    db: Session,
    admin: Admin,
    work_id: int,
    action: ModerationAction,
    reason: str | None = None,
) -> Work:
    work = _get_locked_work(db, work_id)
    work.status = next_status(action, work.status)

    now = datetime.now(UTC)
    if action is ModerationAction.APPROVE:
        work.approved_at = now
    elif action is ModerationAction.REJECT:
        work.rejection_reason = reason
    elif action is ModerationAction.ARCHIVE:
        work.archived_at = now
    elif action is ModerationAction.UNARCHIVE:
        work.archived_at = None

    record_action(
        db,
        admin_id=admin.id,
        target_type=ModerationTarget.WORK,
        target_id=work.id,
        action=action,
        reason=reason,
    )
    db.commit()  # estado + log de auditoria na mesma transação
    logger.info("Admin %s aplicou '%s' na obra %s", admin.id, action.value, work.id)
    return work


def delete_work(db: Session, storage: StorageService, admin: Admin, work_id: int) -> None:
    """Exclusão definitiva. O log de moderação sobrevive (só guarda o id, sem dados pessoais).

    O banco é apagado primeiro: se a remoção dos arquivos falhar, sobram arquivos órfãos
    (inofensivos e registrados no log), em vez de uma obra apontando para arquivos inexistentes."""
    work = _get_locked_work(db, work_id)
    paths = storage_paths([work])
    record_action(
        db,
        admin_id=admin.id,
        target_type=ModerationTarget.WORK,
        target_id=work.id,
        action=ModerationAction.DELETE,
    )
    db.delete(work)
    db.commit()
    storage.delete_quietly(paths)
    logger.info("Admin %s excluiu definitivamente a obra %s", admin.id, work_id)
