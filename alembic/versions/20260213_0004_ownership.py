"""Add ownership fields for courses and paths.

Revision ID: 20260213_0004
Revises: 20260213_0003
Create Date: 2026-02-13
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op


revision = "20260213_0004"
down_revision = "20260213_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add created_by ownership columns."""
    op.add_column("courses", sa.Column("created_by", sa.Text(), nullable=True))
    op.add_column("paths", sa.Column("created_by", sa.Text(), nullable=True))

    op.create_foreign_key(
        "fk_courses_created_by_users_username",
        "courses",
        "users",
        ["created_by"],
        ["username"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_paths_created_by_users_username",
        "paths",
        "users",
        ["created_by"],
        ["username"],
        ondelete="SET NULL",
    )
    op.create_index("idx_courses_created_by", "courses", ["created_by"])
    op.create_index("idx_paths_created_by", "paths", ["created_by"])


def downgrade() -> None:
    """Drop ownership columns and constraints."""
    op.drop_index("idx_paths_created_by", table_name="paths")
    op.drop_index("idx_courses_created_by", table_name="courses")
    op.drop_constraint("fk_paths_created_by_users_username", "paths", type_="foreignkey")
    op.drop_constraint("fk_courses_created_by_users_username", "courses", type_="foreignkey")
    op.drop_column("paths", "created_by")
    op.drop_column("courses", "created_by")
