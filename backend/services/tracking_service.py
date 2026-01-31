from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.database.db import get_conn


STATUS_VALUES = {"interested", "in_progress", "completed"}


def list_tracking(colleague_id: Optional[str] = None) -> List[Dict[str, str]]:
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


def upsert_tracking(colleague_id: str, course_id: int, status: str) -> Dict[str, str]:
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
