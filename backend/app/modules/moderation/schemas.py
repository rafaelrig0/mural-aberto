from datetime import datetime

from pydantic import Field, field_validator

from app.core.schemas import AppSchema
from app.modules.moderation.models import ModerationAction, ModerationTarget


class RejectionRequest(AppSchema):
    reason: str = Field(min_length=3, max_length=1000)


class OptionalRejectionRequest(AppSchema):
    reason: str | None = Field(default=None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        """Motivo só com espaços vira None (antes era gravado como string vazia)."""
        return value or None


class ModerationLogRead(AppSchema):
    id: int
    admin_id: int
    admin_email: str
    target_type: ModerationTarget
    target_id: int
    action: ModerationAction
    reason: str | None
    created_at: datetime
