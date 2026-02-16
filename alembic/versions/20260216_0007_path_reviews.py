"""Add path reviews.

Revision ID: 20260216_0007
Revises: 20260214_0006
Create Date: 2026-02-16
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op


revision = "20260216_0007"
down_revision = "20260214_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create path_reviews table."""
    op.create_table(
        "path_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("path_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["path_id"], ["paths.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.username"], ondelete="CASCADE"),
        sa.UniqueConstraint("path_id", "created_by", name="uq_path_reviews_path_created_by"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_path_reviews_rating"),
    )
    op.create_index("idx_path_reviews_path_id", "path_reviews", ["path_id"])


def downgrade() -> None:
    """Drop path_reviews table."""
    op.drop_index("idx_path_reviews_path_id", table_name="path_reviews")
    op.drop_table("path_reviews")
