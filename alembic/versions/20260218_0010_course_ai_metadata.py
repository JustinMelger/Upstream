"""add optional AI-ready course metadata fields

Revision ID: 20260218_0010
Revises: 20260217_0009
Create Date: 2026-02-18 20:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260218_0010"
down_revision: str | Sequence[str] | None = "20260217_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add optional AI-ready metadata fields to courses."""
    op.add_column("courses", sa.Column("learning_outcomes", sa.Text(), nullable=True))
    op.add_column("courses", sa.Column("prerequisites", sa.Text(), nullable=True))
    op.add_column("courses", sa.Column("language", sa.Text(), nullable=True))


def downgrade() -> None:
    """Drop optional AI-ready metadata fields from courses."""
    op.drop_column("courses", "language")
    op.drop_column("courses", "prerequisites")
    op.drop_column("courses", "learning_outcomes")
