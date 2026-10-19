import pytest

from app.core.exceptions import InvalidTransitionError
from app.modules.comments import state as comment_state
from app.modules.comments.models import CommentStatus
from app.modules.moderation.models import ModerationAction as Action
from app.modules.works import state as work_state
from app.modules.works.models import WorkStatus as W


@pytest.mark.parametrize(
    ("action", "current", "expected"),
    [
        (Action.APPROVE, W.PENDING, W.APPROVED),
        (Action.REJECT, W.PENDING, W.REJECTED),
        (Action.ARCHIVE, W.APPROVED, W.ARCHIVED),
        (Action.UNARCHIVE, W.ARCHIVED, W.APPROVED),
    ],
)
def test_valid_work_transitions(action: Action, current: W, expected: W) -> None:
    assert work_state.next_status(action, current) is expected


@pytest.mark.parametrize(
    ("action", "current"),
    [
        (Action.APPROVE, W.APPROVED),
        (Action.APPROVE, W.REJECTED),  # rejeitada é estado final
        (Action.APPROVE, W.ARCHIVED),
        (Action.REJECT, W.APPROVED),
        (Action.REJECT, W.REJECTED),
        (Action.ARCHIVE, W.PENDING),
        (Action.ARCHIVE, W.REJECTED),
        (Action.UNARCHIVE, W.APPROVED),
        (Action.UNARCHIVE, W.PENDING),
    ],
)
def test_invalid_work_transitions(action: Action, current: W) -> None:
    with pytest.raises(InvalidTransitionError):
        work_state.next_status(action, current)


def test_comment_transitions() -> None:
    assert (
        comment_state.next_status(Action.APPROVE, CommentStatus.PENDING) is CommentStatus.APPROVED
    )
    assert comment_state.next_status(Action.REJECT, CommentStatus.PENDING) is CommentStatus.REJECTED
    for current in (CommentStatus.APPROVED, CommentStatus.REJECTED):
        for action in (Action.APPROVE, Action.REJECT):
            with pytest.raises(InvalidTransitionError):
                comment_state.next_status(action, current)
