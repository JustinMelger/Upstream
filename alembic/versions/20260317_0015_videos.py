"""Add videos table.

Revision ID: 20260317_0015
Revises: 20260228_0014
Create Date: 2026-03-17
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op


revision = "20260317_0015"
down_revision = "20260228_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create videos table."""
    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("provider", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.username"], ondelete="CASCADE"),
    )
    op.create_index("idx_videos_created_by", "videos", ["created_by"])
    op.create_index("idx_videos_url", "videos", ["url"])


def downgrade() -> None:
    """Drop videos table."""
    op.drop_index("idx_videos_url", table_name="videos")
    op.drop_index("idx_videos_created_by", table_name="videos")
    op.drop_table("videos")
