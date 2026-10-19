import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAt, enum_column

if TYPE_CHECKING:
    from app.modules.works.models import Work


class CommentStatus(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (Index("ix_comments_work_id_status", "work_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id", ondelete="CASCADE"))
    author_name: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[CommentStatus] = mapped_column(
        enum_column(CommentStatus),
        default=CommentStatus.PENDING,
        server_default=CommentStatus.PENDING.value,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)  # opcional
    created_at: Mapped[CreatedAt]

    work: Mapped["Work"] = relationship(back_populates="comments")
