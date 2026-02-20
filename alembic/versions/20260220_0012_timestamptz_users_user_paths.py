"""migrate users/user_paths timestamps to timestamptz

Revision ID: 20260220_0012
Revises: 20260220_0011
Create Date: 2026-02-20 18:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260220_0012"
down_revision: str | Sequence[str] | None = "20260220_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Convert selected user and selected-path timestamp columns to timestamptz."""
    op.alter_column(
        "users",
        "created_at",
        existing_type=sa.Text(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        postgresql_using="created_at::timestamptz",
    )
    op.alter_column(
        "users",
        "updated_at",
        existing_type=sa.Text(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        postgresql_using="updated_at::timestamptz",
    )
    op.alter_column(
        "users",
        "last_login_at",
        existing_type=sa.Text(),
        type_=sa.DateTime(timezone=True),
        nullable=True,
        postgresql_using="last_login_at::timestamptz",
    )
    op.alter_column(
        "user_paths",
        "created_at",
        existing_type=sa.Text(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        postgresql_using="created_at::timestamptz",
    )
    op.alter_column(
        "user_paths",
        "updated_at",
        existing_type=sa.Text(),
        type_=sa.DateTime(timezone=True),
        nullable=True,
        postgresql_using="updated_at::timestamptz",
    )


def downgrade() -> None:
    """Revert selected user and selected-path timestamp columns back to text."""
    op.alter_column(
        "user_paths",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.Text(),
        nullable=True,
        postgresql_using="updated_at::text",
    )
    op.alter_column(
        "user_paths",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.Text(),
        nullable=False,
        postgresql_using="created_at::text",
    )
    op.alter_column(
        "users",
        "last_login_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.Text(),
        nullable=True,
        postgresql_using="last_login_at::text",
    )
    op.alter_column(
        "users",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.Text(),
        nullable=False,
        postgresql_using="updated_at::text",
    )
    op.alter_column(
        "users",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.Text(),
        nullable=False,
        postgresql_using="created_at::text",
    )
