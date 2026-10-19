from datetime import date, datetime
from typing import Any, Self

from pydantic import EmailStr, Field, field_validator, model_validator

from app.core.schemas import AppSchema
from app.modules.categories.schemas import CategoryRead
from app.modules.comments.schemas import CommentPublic
from app.modules.works.models import WorkStatus, WorkType

MAX_BODY_TEXT_LENGTH = 50_000


class WorkSubmission(AppSchema):
    """Dados textuais do envio (vêm de um formulário multipart, junto com os arquivos)."""

    title: str = Field(min_length=1, max_length=200)
    author_name: str = Field(min_length=1, max_length=120)
    contact_email: EmailStr
    category_id: int
    work_type: WorkType
    created_on: date
    neighborhood: str | None = Field(default=None, max_length=100)
    body_text: str | None = Field(default=None, max_length=MAX_BODY_TEXT_LENGTH)
    alt_text: str | None = Field(default=None, max_length=500)
    usage_authorized: bool

    @field_validator("neighborhood", "body_text", "alt_text", mode="before")
    @classmethod
    def blank_to_none(cls, value: Any) -> Any:
        """Formulários HTML enviam campos opcionais vazios como string vazia."""
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("usage_authorized")
    @classmethod
    def usage_must_be_authorized(cls, value: bool) -> bool:
        if not value:
            raise ValueError("É necessário autorizar o uso da obra para enviá-la.")
        return value

    @model_validator(mode="after")
    def body_text_matches_work_type(self) -> Self:
        if self.work_type is WorkType.TEXT and self.body_text is None:
            raise ValueError("Obras textuais exigem o campo 'body_text'.")
        if self.work_type is WorkType.VISUAL and self.body_text is not None:
            raise ValueError("Obras visuais não aceitam 'body_text'.")
        return self


class WorkReceived(AppSchema):
    id: int
    status: WorkStatus


class WorkBase(AppSchema):
    id: int
    title: str
    author_name: str
    category: CategoryRead
    work_type: WorkType
    created_on: date
    neighborhood: str | None
    alt_text: str | None
    image_url: str | None
    video_url: str | None
    approved_at: datetime | None


class WorkPublicSummary(WorkBase):
    excerpt: str | None


class WorkPublicDetail(WorkBase):
    body_text: str | None
    comments: list[CommentPublic]


class WorkAdmin(WorkBase):
    """Visão administrativa. É a única que inclui o e-mail de contato."""

    body_text: str | None
    contact_email: str
    status: WorkStatus
    rejection_reason: str | None
    usage_authorized_at: datetime
    archived_at: datetime | None
    created_at: datetime
