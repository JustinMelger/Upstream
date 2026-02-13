"""Add articles table.

Revision ID: 20260213_0003
Revises: 20260209_0002
Create Date: 2026-02-13
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op


revision = "20260213_0003"
down_revision = "20260209_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create articles table."""
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.username"], ondelete="CASCADE"),
    )
    op.create_index("idx_articles_created_by", "articles", ["created_by"])
    op.create_index("idx_articles_url", "articles", ["url"])


def downgrade() -> None:
    """Drop articles table."""
    op.drop_index("idx_articles_url", table_name="articles")
    op.drop_index("idx_articles_created_by", table_name="articles")
    op.drop_table("articles")
