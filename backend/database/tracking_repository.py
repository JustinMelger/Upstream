from __future__ import annotations

from backend.database.db import SQLiteDatabase
from backend.database.models import TrackingRecord


class SQLiteTrackingRepository:
    """SQLite implementation of tracking persistence."""

    def __init__(self, db: SQLiteDatabase):
        """Initialize the repository.

        Args:
            db: SQLite database client.
        """
        self._db = db

    def list_tracking(self, colleague_id: str | None) -> list[TrackingRecord]:
        """List tracking entries, optionally filtered by colleague.

        Args:
            colleague_id: Optional colleague username.

        Returns:
            Tracking records.
        """
        sql = "SELECT colleague_id, course_id, status, updated_at FROM tracking"
        params: list[str] = []
        if colleague_id:
            sql += " WHERE colleague_id = ?"
            params.append(colleague_id)

        with self._db.get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        return [
            TrackingRecord(
                colleague_id=row["colleague_id"],
                course_id=int(row["course_id"]),
                status=row["status"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def list_recent_activity(self, limit: int) -> list[TrackingRecord]:
        """List recent tracking activity."""
        with self._db.get_conn() as conn:
            rows = conn.execute(
                """
                SELECT colleague_id, course_id, status, updated_at
                FROM tracking
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            TrackingRecord(
                colleague_id=row["colleague_id"],
                course_id=int(row["course_id"]),
                status=row["status"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def stats_for_colleague(self, colleague_id: str) -> dict[str, int]:
        """Get tracking stats for a colleague."""
        with self._db.get_conn() as conn:
            rows = conn.execute(
                """
                SELECT status, COUNT(*) as count
                FROM tracking
                WHERE colleague_id = ?
                GROUP BY status
                """,
                (colleague_id,),
            ).fetchall()
        return {row["status"]: row["count"] for row in rows}

    def stats_all(self) -> dict[str, int]:
        """Get tracking stats for all users."""
        with self._db.get_conn() as conn:
            rows = conn.execute(
                """
                SELECT status, COUNT(*) as count
                FROM tracking
                GROUP BY status
                """
            ).fetchall()
        return {row["status"]: row["count"] for row in rows}

    def stats_by_user(self) -> list[dict]:
        """Get tracking stats grouped by user."""
        with self._db.get_conn() as conn:
            rows = conn.execute(
                """
                SELECT colleague_id, status, COUNT(*) as count
                FROM tracking
                GROUP BY colleague_id, status
                ORDER BY colleague_id ASC
                """
            ).fetchall()

        by_user: dict[str, dict[str, int]] = {}
        for row in rows:
            user = row["colleague_id"]
            by_user.setdefault(user, {"interested": 0, "in_progress": 0, "completed": 0})
            by_user[user][row["status"]] = row["count"]

        return [
            {
                "colleague_id": user,
                "interested": stats["interested"],
                "in_progress": stats["in_progress"],
                "completed": stats["completed"],
            }
            for user, stats in by_user.items()
        ]

    def upsert_tracking(self, colleague_id: str, course_id: int, status: str, updated_at: str) -> None:
        """Insert or update a tracking status."""
        with self._db.get_conn() as conn:
            conn.execute(
                """
                INSERT INTO tracking (colleague_id, course_id, status, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(colleague_id, course_id)
                DO UPDATE SET status = excluded.status, updated_at = excluded.updated_at
                """,
                (colleague_id, course_id, status, updated_at),
            )
            conn.commit()

    def remove_tracking(self, colleague_id: str, course_id: int) -> int:
        """Remove a tracking record."""
        with self._db.get_conn() as conn:
            cur = conn.execute(
                """
                DELETE FROM tracking
                WHERE colleague_id = ? AND course_id = ?
                """,
                (colleague_id, course_id),
            )
            conn.commit()
            return cur.rowcount
