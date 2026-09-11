"""Add optional article summaries for visual discovery."""

import sqlalchemy as sa

from alembic import op


revision = "20260909_0019"
down_revision = "20260909_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Preserve existing content while allowing optional article descriptions."""
    op.add_column("articles", sa.Column("description", sa.Text(), nullable=True))
    op.create_check_constraint("ck_articles_description_length", "articles", "length(description) <= 2000")


def downgrade() -> None:
    """Remove the new summary field only for an explicit schema rollback."""
    op.drop_constraint("ck_articles_description_length", "articles", type_="check")
    op.drop_column("articles", "description")
