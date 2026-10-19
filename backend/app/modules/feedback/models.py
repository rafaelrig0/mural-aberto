import enum

from sqlalchemy import CheckConstraint, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAt, enum_column


class FeedbackType(enum.StrEnum):
    OPINION = "opinion"
    SUGGESTION = "suggestion"
    BUG = "bug"
    OTHER = "other"


class Feedback(Base):
    """Opinião, sugestão ou relato de problema enviado por qualquer visitante (sem cadastro)."""

    __tablename__ = "feedbacks"
    __table_args__ = (
        CheckConstraint("rating IS NULL OR rating BETWEEN 1 AND 5", name="rating_between_1_and_5"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    author_name: Mapped[str | None] = mapped_column(String(120))  # opcional
    feedback_type: Mapped[FeedbackType] = mapped_column(enum_column(FeedbackType))
    message: Mapped[str] = mapped_column(Text)
    rating: Mapped[int | None] = mapped_column(SmallInteger)  # opcional, de 1 a 5
    created_at: Mapped[CreatedAt]
