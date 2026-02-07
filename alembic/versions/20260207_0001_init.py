"""Initial schema.

Revision ID: 20260207_0001
Revises:
Create Date: 2026-02-07
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op


revision = "20260207_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("level", sa.Text(), nullable=True),
        sa.Column("duration_hours", sa.Float(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=True),
    )

    op.create_table(
        "tracking",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("colleague_id", sa.Text(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.UniqueConstraint("colleague_id", "course_id", name="uq_tracking_colleague_course"),
    )

    op.create_table(
        "paths",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("name", name="uq_paths_name"),
    )

    op.create_table(
        "path_courses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("path_id", sa.Integer(), sa.ForeignKey("paths.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.UniqueConstraint("path_id", "course_id", name="uq_path_courses_path_course"),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("colleague_id", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("last_seen", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Text(), nullable=False),
    )
    op.create_index("idx_sessions_token", "sessions", ["token_hash"])
    op.create_index("idx_sessions_colleague", "sessions", ["colleague_id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("last_login_at", sa.Text(), nullable=True),
        sa.Column("disabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.CheckConstraint("role in ('admin', 'user')", name="ck_users_role"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("idx_users_username", "users", ["username"])

    op.create_table(
        "user_paths",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("colleague_id", sa.Text(), nullable=False),
        sa.Column("path_id", sa.Integer(), sa.ForeignKey("paths.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.UniqueConstraint("colleague_id", "path_id", name="uq_user_paths_colleague_path"),
    )


def downgrade() -> None:
    op.drop_table("user_paths")
    op.drop_index("idx_users_username", table_name="users")
    op.drop_table("users")
    op.drop_index("idx_sessions_colleague", table_name="sessions")
    op.drop_index("idx_sessions_token", table_name="sessions")
    op.drop_table("sessions")
    op.drop_table("path_courses")
    op.drop_table("paths")
    op.drop_table("tracking")
    op.drop_table("courses")
