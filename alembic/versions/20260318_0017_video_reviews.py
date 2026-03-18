"""Add video reviews table.

Revision ID: 20260318_0017
Revises: 20260318_0016
Create Date: 2026-03-18
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op


revision = "20260318_0017"
down_revision = "20260318_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create video_reviews with moderation-friendly ownership constraints."""
    op.create_table(
        "video_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_video_reviews_rating"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.username"], ondelete="CASCADE"),
        sa.UniqueConstraint("video_id", "created_by", name="uq_video_reviews_video_created_by"),
    )
    op.create_index("idx_video_reviews_video_id", "video_reviews", ["video_id"])


def downgrade() -> None:
    """Drop video review persistence."""
    op.drop_index("idx_video_reviews_video_id", table_name="video_reviews")
    op.drop_table("video_reviews")
