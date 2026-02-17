"""Add article reviews.

Revision ID: 20260217_0008
Revises: 20260216_0007
Create Date: 2026-02-17
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op


revision = "20260217_0008"
down_revision = "20260216_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create article_reviews table."""
    op.create_table(
        "article_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.username"], ondelete="CASCADE"),
        sa.UniqueConstraint("article_id", "created_by", name="uq_article_reviews_article_created_by"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_article_reviews_rating"),
    )
    op.create_index("idx_article_reviews_article_id", "article_reviews", ["article_id"])


def downgrade() -> None:
    """Drop article_reviews table."""
    op.drop_index("idx_article_reviews_article_id", table_name="article_reviews")
    op.drop_table("article_reviews")
