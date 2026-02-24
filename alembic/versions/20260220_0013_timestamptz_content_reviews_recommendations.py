"""migrate content/review/recommendation timestamps to timestamptz

Revision ID: 20260220_0013
Revises: 20260220_0012
Create Date: 2026-02-20 19:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260220_0013"
down_revision: str | Sequence[str] | None = "20260220_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _to_timestamptz(table: str, column: str, *, nullable: bool) -> None:
    op.alter_column(
        table,
        column,
        existing_type=sa.Text(),
        type_=sa.DateTime(timezone=True),
        nullable=nullable,
        postgresql_using=f"{column}::timestamptz",
    )


def _to_text(table: str, column: str, *, nullable: bool) -> None:
    op.alter_column(
        table,
        column,
        existing_type=sa.DateTime(timezone=True),
        type_=sa.Text(),
        nullable=nullable,
        postgresql_using=f"{column}::text",
    )


def upgrade() -> None:
    """Convert content/review/recommendation created_at columns to timestamptz."""
    _to_timestamptz("courses", "created_at", nullable=True)
    _to_timestamptz("articles", "created_at", nullable=False)

    _to_timestamptz("course_reviews", "created_at", nullable=False)
    _to_timestamptz("path_reviews", "created_at", nullable=False)
    _to_timestamptz("article_reviews", "created_at", nullable=False)

    _to_timestamptz("course_recommendations", "created_at", nullable=False)
    _to_timestamptz("path_recommendations", "created_at", nullable=False)


def downgrade() -> None:
    """Revert content/review/recommendation created_at columns back to text."""
    _to_text("path_recommendations", "created_at", nullable=False)
    _to_text("course_recommendations", "created_at", nullable=False)

    _to_text("article_reviews", "created_at", nullable=False)
    _to_text("path_reviews", "created_at", nullable=False)
    _to_text("course_reviews", "created_at", nullable=False)

    _to_text("articles", "created_at", nullable=False)
    _to_text("courses", "created_at", nullable=True)
