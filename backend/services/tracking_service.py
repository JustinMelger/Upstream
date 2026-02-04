from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.database.db import get_conn


STATUS_VALUES = {"interested", "in_progress", "completed"}


def list_tracking(colleague_id: Optional[str] = None) -> List[Dict[str, str]]:
    """List tracking entries, optionally filtered by colleague.

    Args:
        colleague_id: Optional colleague username.

    Returns:
        list[dict]: Tracking entries.
    """
    sql = "SELECT colleague_id, course_id, status, updated_at FROM tracking"
    params: List[str] = []
    if colleague_id:
        sql += " WHERE colleague_id = ?"
        params.append(colleague_id)

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [
        {
            "colleague_id": row["colleague_id"],
            "course_id": str(row["course_id"]),
            "status": row["status"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def list_recent_activity(limit: int = 10) -> List[Dict[str, str]]:
    """List recent tracking activity.

    Args:
        limit: Max number of records.

    Returns:
        list[dict]: Recent tracking entries.
    """
    with get_conn() as conn:
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
        {
            "colleague_id": row["colleague_id"],
            "course_id": str(row["course_id"]),
            "status": row["status"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def stats_for_colleague(colleague_id: str) -> Dict[str, int]:
    """Get tracking stats for a colleague.

    Args:
        colleague_id: Colleague username.

    Returns:
        dict: Status counts.
    """
    with get_conn() as conn:
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


def stats_all() -> Dict[str, int]:
    """Get tracking stats for all users.

    Returns:
        dict: Status counts.
    """
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT status, COUNT(*) as count
            FROM tracking
            GROUP BY status
            """
        ).fetchall()

    return {row["status"]: row["count"] for row in rows}


def stats_by_user() -> List[Dict[str, int | str]]:
    """Get tracking stats grouped by user.

    Returns:
        list[dict]: Per-user status counts.
    """
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT colleague_id, status, COUNT(*) as count
            FROM tracking
            GROUP BY colleague_id, status
            ORDER BY colleague_id ASC
            """
        ).fetchall()

    by_user: Dict[str, Dict[str, int]] = {}
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


def upsert_tracking(colleague_id: str, course_id: int, status: str) -> Dict[str, str]:
    """Insert or update a tracking status.

    Args:
        colleague_id: Colleague username.
        course_id: Course ID.
        status: Tracking status.

    Returns:
        dict: Tracking record.
    """
    if status not in STATUS_VALUES:
        raise ValueError("invalid_status")

    now = datetime.now(timezone.utc).isoformat()

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO tracking (colleague_id, course_id, status, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(colleague_id, course_id)
            DO UPDATE SET status = excluded.status, updated_at = excluded.updated_at
            """,
            (colleague_id, course_id, status, now),
        )
        conn.commit()

    return {
        "colleague_id": colleague_id,
        "course_id": str(course_id),
        "status": status,
        "updated_at": now,
    }


def remove_tracking(colleague_id: str, course_id: int) -> int:
    """Remove a tracking record.

    Args:
        colleague_id: Colleague username.
        course_id: Course ID.

    Returns:
        int: Number of rows removed.
    """
    with get_conn() as conn:
        cur = conn.execute(
            """
            DELETE FROM tracking
            WHERE colleague_id = ? AND course_id = ?
            """,
            (colleague_id, course_id),
        )
        conn.commit()

    return cur.rowcount
