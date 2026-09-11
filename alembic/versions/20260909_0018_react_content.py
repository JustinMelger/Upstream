"""Add author recommendation notes and timestamps for future path shares.

Existing paths remain undated instead of inventing historical activity.
"""

import sqlalchemy as sa

from alembic import op


revision = "20260909_0018"
down_revision = "20260318_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add nullable notes without altering existing learning records."""
    for table in ("courses", "articles", "videos", "paths"):
        op.add_column(table, sa.Column("recommendation_note", sa.Text(), nullable=True))
        op.create_check_constraint(f"ck_{table}_note_length", table, "length(recommendation_note) <= 1000")
    op.add_column("paths", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("paths", "created_at", server_default=sa.text("CURRENT_TIMESTAMP"))


def downgrade() -> None:
    """Remove newly introduced metadata; core records are retained."""
    op.drop_column("paths", "created_at")
    for table in ("courses", "articles", "videos", "paths"):
        op.drop_constraint(f"ck_{table}_note_length", table, type_="check")
        op.drop_column(table, "recommendation_note")
