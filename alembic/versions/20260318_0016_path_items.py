"""Replace path_courses with typed path_items.

Revision ID: 20260318_0016
Revises: 20260317_0015
Create Date: 2026-03-18
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op


revision = "20260318_0016"
down_revision = "20260317_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create typed path_items and migrate legacy course rows."""
    op.create_table(
        "path_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("path_id", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.Text(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.CheckConstraint("item_type in ('course', 'video', 'article')", name="ck_path_items_type"),
        sa.ForeignKeyConstraint(["path_id"], ["paths.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("path_id", "item_type", "item_id", name="uq_path_items_path_type_item"),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO path_items (path_id, item_type, item_id, position)
            SELECT path_id, 'course', course_id, position
            FROM path_courses
            """
        )
    )
    op.drop_table("path_courses")


def downgrade() -> None:
    """Restore legacy path_courses from course-backed path items."""
    op.create_table(
        "path_courses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("path_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["path_id"], ["paths.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("path_id", "course_id", name="uq_path_courses_path_course"),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO path_courses (path_id, course_id, position)
            SELECT path_id, item_id, position
            FROM path_items
            WHERE item_type = 'course'
            """
        )
    )
    op.drop_table("path_items")
