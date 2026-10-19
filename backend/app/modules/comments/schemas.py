from datetime import datetime

from pydantic import Field

from app.core.schemas import AppSchema, ORMSchema
from app.modules.comments.models import CommentStatus

MAX_COMMENT_LENGTH = 2000


class CommentCreate(AppSchema):
    author_name: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=MAX_COMMENT_LENGTH)


class CommentPublic(ORMSchema):
    id: int
    author_name: str
    content: str
    created_at: datetime


class CommentReceived(AppSchema):
    id: int
    status: CommentStatus


class CommentAdmin(ORMSchema):
    id: int
    work_id: int
    author_name: str
    content: str
    status: CommentStatus
    rejection_reason: str | None
    created_at: datetime
