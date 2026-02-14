"""Add required course description.

Revision ID: 20260213_0005
Revises: 20260213_0004
Create Date: 2026-02-13
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op


revision = "20260213_0005"
down_revision = "20260213_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add `courses.description` (required)."""
    # Use a server default so existing rows/migrations remain non-breaking.
    op.add_column("courses", sa.Column("description", sa.Text(), nullable=False, server_default=""))
    # Optional: drop the server default after backfill (kept for simplicity).


def downgrade() -> None:
    """Drop `courses.description`."""
    op.drop_column("courses", "description")
