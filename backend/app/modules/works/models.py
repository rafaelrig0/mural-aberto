import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAt, enum_column

if TYPE_CHECKING:
    from app.modules.categories.models import Category
    from app.modules.comments.models import Comment
    from app.modules.media.models import WorkMedia


class WorkType(enum.StrEnum):
    VISUAL = "visual"
    TEXT = "text"


class WorkStatus(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class Work(Base):
    __tablename__ = "works"
    __table_args__ = (
        CheckConstraint("work_type <> 'text' OR body_text IS NOT NULL", name="text_work_has_body"),
        CheckConstraint(
            "status <> 'rejected' OR rejection_reason IS NOT NULL", name="rejected_has_reason"
        ),
        Index("ix_works_status_approved_at", "status", "approved_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author_name: Mapped[str] = mapped_column(String(120))
    contact_email: Mapped[str] = mapped_column(String(254))  # privado: nunca em schema público
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True
    )
    work_type: Mapped[WorkType] = mapped_column(enum_column(WorkType))
    created_on: Mapped[date] = mapped_column(Date)
    neighborhood: Mapped[str | None] = mapped_column(String(100))
    body_text: Mapped[str | None] = mapped_column(Text)
    alt_text: Mapped[str | None] = mapped_column(String(500))
    usage_authorized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[WorkStatus] = mapped_column(
        enum_column(WorkStatus),
        default=WorkStatus.PENDING,
        server_default=WorkStatus.PENDING.value,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[CreatedAt]

    category: Mapped["Category"] = relationship()
    media: Mapped[list["WorkMedia"]] = relationship(
        back_populates="work", cascade="all, delete-orphan", passive_deletes=True
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="work", cascade="all, delete-orphan", passive_deletes=True
    )
