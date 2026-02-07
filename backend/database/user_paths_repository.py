from __future__ import annotations

from backend.database.db import SQLiteDatabase
from backend.database.models import SelectedPathRecord


class SQLiteUserPathsRepository:
    """SQLite implementation of user path selection persistence."""

    def __init__(self, db: SQLiteDatabase):
        """Initialize the repository.

        Args:
            db: SQLite database client.
        """
        self._db = db

    def add_user_path(self, colleague_id: str, path_id: int, now: str) -> int:
        """Insert a user_path selection if missing."""
        with self._db.get_conn() as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO user_paths (colleague_id, path_id, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (colleague_id, path_id, now, now),
            )
            conn.commit()
            return cur.rowcount

    def list_user_paths(self, colleague_id: str) -> list[SelectedPathRecord]:
        """List selected paths for a user."""
        with self._db.get_conn() as conn:
            rows = conn.execute(
                """
                SELECT p.id, p.name, p.description, up.status
                FROM user_paths up
                JOIN paths p ON p.id = up.path_id
                WHERE up.colleague_id = ?
                ORDER BY p.name ASC
                """,
                (colleague_id,),
            ).fetchall()
        return [
            SelectedPathRecord(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                status=row["status"],
            )
            for row in rows
        ]

    def remove_user_path(self, colleague_id: str, path_id: int) -> int:
        """Remove a selected path."""
        with self._db.get_conn() as conn:
            cur = conn.execute(
                """
                DELETE FROM user_paths
                WHERE colleague_id = ? AND path_id = ?
                """,
                (colleague_id, path_id),
            )
            conn.commit()
            return cur.rowcount

    def update_user_path_status(self, colleague_id: str, path_id: int, status: str, now: str) -> int:
        """Update status for a selected path."""
        with self._db.get_conn() as conn:
            cur = conn.execute(
                """
                UPDATE user_paths
                SET status = ?, updated_at = ?
                WHERE colleague_id = ? AND path_id = ?
                """,
                (status, now, colleague_id, path_id),
            )
            conn.commit()
            return cur.rowcount
