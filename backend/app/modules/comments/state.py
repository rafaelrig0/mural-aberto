from app.core.exceptions import InvalidTransitionError
from app.modules.comments.models import CommentStatus
from app.modules.moderation.models import ModerationAction

TRANSITIONS: dict[ModerationAction, tuple[frozenset[CommentStatus], CommentStatus]] = {
    ModerationAction.APPROVE: (frozenset({CommentStatus.PENDING}), CommentStatus.APPROVED),
    ModerationAction.REJECT: (frozenset({CommentStatus.PENDING}), CommentStatus.REJECTED),
}


def next_status(action: ModerationAction, current: CommentStatus) -> CommentStatus:
    allowed_from, target = TRANSITIONS[action]
    if current not in allowed_from:
        raise InvalidTransitionError(
            f"Não é possível aplicar '{action.value}' a um comentário com estado '{current.value}'."
        )
    return target
