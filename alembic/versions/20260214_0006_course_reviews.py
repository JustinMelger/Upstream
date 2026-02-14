"""Add course reviews.

Revision ID: 20260214_0006
Revises: 20260213_0005
Create Date: 2026-02-14
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op


revision = "20260214_0006"
down_revision = "20260213_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create course_reviews table."""
    op.create_table(
        "course_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.username"], ondelete="CASCADE"),
        sa.UniqueConstraint("course_id", "created_by", name="uq_course_reviews_course_created_by"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_course_reviews_rating"),
    )
    op.create_index("idx_course_reviews_course_id", "course_reviews", ["course_id"])


def downgrade() -> None:
    """Drop course_reviews table."""
    op.drop_index("idx_course_reviews_course_id", table_name="course_reviews")
    op.drop_table("course_reviews")
