from datetime import datetime, timezone
from typing import Dict, List

from backend.database.db import get_conn


STATUS_VALUES = {"interested", "in_progress", "completed"}


def add_user_path(colleague_id: str, path_id: int) -> Dict[str, str]:
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO user_paths (colleague_id, path_id, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (colleague_id, path_id, now, now),
        )
        conn.commit()

    return {"colleague_id": colleague_id, "path_id": str(path_id), "created_at": now}


def list_user_paths(colleague_id: str) -> List[Dict[str, str]]:
    with get_conn() as conn:
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
        {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"] or "",
            "status": row["status"] or "",
        }
        for row in rows
    ]


def remove_user_path(colleague_id: str, path_id: int) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            DELETE FROM user_paths
            WHERE colleague_id = ? AND path_id = ?
            """,
            (colleague_id, path_id),
        )
        conn.commit()

    return cur.rowcount


def update_user_path_status(colleague_id: str, path_id: int, status: str) -> int:
    if status not in STATUS_VALUES:
        raise ValueError("invalid_status")

    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
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
