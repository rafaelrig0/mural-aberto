from collections.abc import Iterable, Sequence

from app.modules.categories.schemas import CategoryRead
from app.modules.comments.models import Comment
from app.modules.comments.schemas import CommentPublic
from app.modules.media.models import MediaKind
from app.modules.works.models import Work
from app.modules.works.schemas import WorkAdmin, WorkPublicDetail, WorkPublicSummary

EXCERPT_LENGTH = 200


def _media_url(work: Work, kind: MediaKind, urls: dict[str, str]) -> str | None:
    for media in work.media:
        if media.kind is kind:
            return urls.get(media.storage_path)
    return None


def _excerpt(text: str | None) -> str | None:
    if text is None:
        return None
    return text if len(text) <= EXCERPT_LENGTH else text[:EXCERPT_LENGTH].rstrip() + "…"


def _base_fields(work: Work, urls: dict[str, str]) -> dict[str, object]:
    return {
        "id": work.id,
        "title": work.title,
        "author_name": work.author_name,
        "category": CategoryRead.model_validate(work.category),
        "work_type": work.work_type,
        "created_on": work.created_on,
        "neighborhood": work.neighborhood,
        "alt_text": work.alt_text,
        "image_url": _media_url(work, MediaKind.IMAGE, urls),
        "video_url": _media_url(work, MediaKind.VIDEO, urls),
        "approved_at": work.approved_at,
    }


def to_public_summary(work: Work, urls: dict[str, str]) -> WorkPublicSummary:
    return WorkPublicSummary(**_base_fields(work, urls), excerpt=_excerpt(work.body_text))


def to_public_detail(
    work: Work, comments: Iterable[Comment], urls: dict[str, str]
) -> WorkPublicDetail:
    return WorkPublicDetail(
        **_base_fields(work, urls),
        body_text=work.body_text,
        comments=[CommentPublic.model_validate(c) for c in comments],
    )


def to_admin(work: Work, urls: dict[str, str]) -> WorkAdmin:
    return WorkAdmin(
        **_base_fields(work, urls),
        body_text=work.body_text,
        contact_email=work.contact_email,
        status=work.status,
        rejection_reason=work.rejection_reason,
        usage_authorized_at=work.usage_authorized_at,
        archived_at=work.archived_at,
        created_at=work.created_at,
    )


def storage_paths(works: Sequence[Work]) -> list[str]:
    return [media.storage_path for work in works for media in work.media]
