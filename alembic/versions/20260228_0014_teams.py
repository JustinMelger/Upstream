"""add teams and team_members tables

Revision ID: 20260228_0014
Revises: 20260220_0013
Create Date: 2026-02-28 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "20260228_0014"
down_revision: str | Sequence[str] | None = "20260220_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create team and team-membership tables."""
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_user_id", sa.Text(), sa.ForeignKey("users.username", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_teams_owner", "teams", ["owner_user_id"])

    op.create_table(
        "team_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.username", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role in ('owner', 'admin', 'member')", name="ck_team_members_role"),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_members_team_user"),
    )
    op.create_index("idx_team_members_user", "team_members", ["user_id"])
    op.create_index("idx_team_members_team", "team_members", ["team_id"])


def downgrade() -> None:
    """Drop team and team-membership tables."""
    op.drop_index("idx_team_members_team", table_name="team_members")
    op.drop_index("idx_team_members_user", table_name="team_members")
    op.drop_table("team_members")

    op.drop_index("idx_teams_owner", table_name="teams")
    op.drop_table("teams")
