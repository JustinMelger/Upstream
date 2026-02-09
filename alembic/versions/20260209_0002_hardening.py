"""Postgres hardening constraints.

Revision ID: 20260209_0002
Revises: 20260207_0001
Create Date: 2026-02-09
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op


revision = "20260209_0002"
down_revision = "20260207_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add domain integrity constraints."""
    op.create_foreign_key(
        "fk_tracking_course_id_courses",
        "tracking",
        "courses",
        ["course_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_path_courses_course_id_courses",
        "path_courses",
        "courses",
        ["course_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_sessions_colleague_id_users_username",
        "sessions",
        "users",
        ["colleague_id"],
        ["username"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint("uq_sessions_token_hash", "sessions", ["token_hash"])


def downgrade() -> None:
    """Drop hardening constraints."""
    op.drop_constraint("uq_sessions_token_hash", "sessions", type_="unique")
    op.drop_constraint("fk_sessions_colleague_id_users_username", "sessions", type_="foreignkey")
    op.drop_constraint("fk_path_courses_course_id_courses", "path_courses", type_="foreignkey")
    op.drop_constraint("fk_tracking_course_id_courses", "tracking", type_="foreignkey")
