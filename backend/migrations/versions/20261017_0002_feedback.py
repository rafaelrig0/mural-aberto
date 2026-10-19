"""feedback

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-17 18:11:04.278892
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("author_name", sa.String(length=120), nullable=True),
        sa.Column(
            "feedback_type",
            sa.Enum(
                "opinion",
                "suggestion",
                "bug",
                "other",
                name="feedbacktype",
                native_enum=False,
                create_constraint=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "feedback_type IN ('opinion', 'suggestion', 'bug', 'other')",
            name=op.f("ck_feedbacks_feedbacktype"),
        ),
        sa.CheckConstraint(
            "rating IS NULL OR rating BETWEEN 1 AND 5",
            name=op.f("ck_feedbacks_rating_between_1_and_5"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedbacks")),
    )
    # Mesmo critério das demais tabelas: RLS ligado e sem políticas bloqueia a API REST
    # automática do Supabase (chave 'anon'); o backend conecta como dono e não é afetado.
    op.execute('ALTER TABLE "feedbacks" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    op.drop_table("feedbacks")
