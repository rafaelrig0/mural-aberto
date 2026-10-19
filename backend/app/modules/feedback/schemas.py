from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.core.schemas import AppSchema, ORMSchema
from app.modules.feedback.models import FeedbackType

MIN_MESSAGE_LENGTH = 5
MAX_MESSAGE_LENGTH = 2000


class FeedbackCreate(AppSchema):
    author_name: str | None = Field(default=None, max_length=120)
    feedback_type: FeedbackType
    message: str = Field(min_length=MIN_MESSAGE_LENGTH, max_length=MAX_MESSAGE_LENGTH)
    rating: int | None = Field(default=None, ge=1, le=5)

    @field_validator("author_name", mode="before")
    @classmethod
    def blank_to_none(cls, value: Any) -> Any:
        """Campo opcional deixado em branco no formulário chega como string vazia."""
        if isinstance(value, str):
            return value.strip() or None
        return value


class FeedbackReceived(AppSchema):
    id: int


class FeedbackAdmin(ORMSchema):
    id: int
    author_name: str | None
    feedback_type: FeedbackType
    message: str
    rating: int | None
    created_at: datetime
