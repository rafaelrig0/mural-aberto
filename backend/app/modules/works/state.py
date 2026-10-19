from app.core.exceptions import InvalidTransitionError
from app.modules.moderation.models import ModerationAction
from app.modules.works.models import WorkStatus

# ação -> (estados de origem permitidos, estado de destino)
TRANSITIONS: dict[ModerationAction, tuple[frozenset[WorkStatus], WorkStatus]] = {
    ModerationAction.APPROVE: (frozenset({WorkStatus.PENDING}), WorkStatus.APPROVED),
    ModerationAction.REJECT: (frozenset({WorkStatus.PENDING}), WorkStatus.REJECTED),  # final
    ModerationAction.ARCHIVE: (frozenset({WorkStatus.APPROVED}), WorkStatus.ARCHIVED),
    ModerationAction.UNARCHIVE: (frozenset({WorkStatus.ARCHIVED}), WorkStatus.APPROVED),
}


def next_status(action: ModerationAction, current: WorkStatus) -> WorkStatus:
    allowed_from, target = TRANSITIONS[action]
    if current not in allowed_from:
        raise InvalidTransitionError(
            f"Não é possível aplicar '{action.value}' a uma obra com estado '{current.value}'."
        )
    return target
