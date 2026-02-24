"""migrate sessions/tracking timestamps to timestamptz

Revision ID: 20260220_0011
Revises: 20260218_0010
Create Date: 2026-02-20 16:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260220_0011"
down_revision: str | Sequence[str] | None = "20260218_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Convert selected text timestamp columns to TIMESTAMP WITH TIME ZONE."""
    op.alter_column(
        "sessions",
        "created_at",
        existing_type=sa.Text(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        postgresql_using="created_at::timestamptz",
    )
    op.alter_column(
        "sessions",
        "last_seen",
        existing_type=sa.Text(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        postgresql_using="last_seen::timestamptz",
    )
    op.alter_column(
        "sessions",
        "expires_at",
        existing_type=sa.Text(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        postgresql_using="expires_at::timestamptz",
    )
    op.alter_column(
        "tracking",
        "updated_at",
        existing_type=sa.Text(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        postgresql_using="updated_at::timestamptz",
    )


def downgrade() -> None:
    """Revert selected timestamp columns back to text."""
    op.alter_column(
        "tracking",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.Text(),
        nullable=False,
        postgresql_using="updated_at::text",
    )
    op.alter_column(
        "sessions",
        "expires_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.Text(),
        nullable=False,
        postgresql_using="expires_at::text",
    )
    op.alter_column(
        "sessions",
        "last_seen",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.Text(),
        nullable=False,
        postgresql_using="last_seen::text",
    )
    op.alter_column(
        "sessions",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.Text(),
        nullable=False,
        postgresql_using="created_at::text",
    )
