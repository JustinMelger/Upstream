"""add course/path recommendations

Revision ID: 20260217_0009
Revises: 20260217_0008
Create Date: 2026-02-17 10:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260217_0009"
down_revision: str | Sequence[str] | None = "20260217_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create course/path recommendation tables."""
    op.create_table(
        "course_recommendations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Text(), sa.ForeignKey("users.username", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.UniqueConstraint("course_id", "created_by", name="uq_course_recommendations_course_created_by"),
    )
    op.create_index("idx_course_recommendations_course_id", "course_recommendations", ["course_id"])

    op.create_table(
        "path_recommendations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("path_id", sa.Integer(), sa.ForeignKey("paths.id", ondelete="CASCADE"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Text(), sa.ForeignKey("users.username", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.UniqueConstraint("path_id", "created_by", name="uq_path_recommendations_path_created_by"),
    )
    op.create_index("idx_path_recommendations_path_id", "path_recommendations", ["path_id"])


def downgrade() -> None:
    """Drop course/path recommendation tables."""
    op.drop_index("idx_path_recommendations_path_id", table_name="path_recommendations")
    op.drop_table("path_recommendations")

    op.drop_index("idx_course_recommendations_course_id", table_name="course_recommendations")
    op.drop_table("course_recommendations")
