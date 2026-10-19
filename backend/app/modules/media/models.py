import enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAt, enum_column

if TYPE_CHECKING:
    from app.modules.works.models import Work


class MediaKind(enum.StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class WorkMedia(Base):
    __tablename__ = "work_media"
    # Garante no banco: no máximo 1 imagem e 1 vídeo por obra.
    __table_args__ = (UniqueConstraint("work_id", "kind"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id", ondelete="CASCADE"))
    kind: Mapped[MediaKind] = mapped_column(enum_column(MediaKind))
    storage_path: Mapped[str] = mapped_column(String(300), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[CreatedAt]

    work: Mapped["Work"] = relationship(back_populates="media")
