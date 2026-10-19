import enum

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAt, enum_column


class ModerationTarget(enum.StrEnum):
    WORK = "work"
    COMMENT = "comment"


class ModerationAction(enum.StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    ARCHIVE = "archive"
    UNARCHIVE = "unarchive"
    DELETE = "delete"


class ModerationLog(Base):
    """Registro append-only. target_id NÃO é FK de propósito: o log precisa
    sobreviver à exclusão definitiva do alvo, sem guardar dados pessoais."""

    __tablename__ = "moderation_logs"
    __table_args__ = (Index("ix_moderation_logs_target", "target_type", "target_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id", ondelete="RESTRICT"))
    target_type: Mapped[ModerationTarget] = mapped_column(enum_column(ModerationTarget))
    target_id: Mapped[int]
    action: Mapped[ModerationAction] = mapped_column(enum_column(ModerationAction))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[CreatedAt]
