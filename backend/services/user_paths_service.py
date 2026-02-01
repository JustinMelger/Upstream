from datetime import datetime, timezone
from typing import Dict, List

from backend.database.db import get_conn


def add_user_path(colleague_id: str, path_id: int) -> Dict[str, str]:
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO user_paths (colleague_id, path_id, created_at)
            VALUES (?, ?, ?)
            """,
            (colleague_id, path_id, now),
        )
        conn.commit()

    return {"colleague_id": colleague_id, "path_id": str(path_id), "created_at": now}


def list_user_paths(colleague_id: str) -> List[Dict[str, str]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT p.id, p.name, p.description
            FROM user_paths up
            JOIN paths p ON p.id = up.path_id
            WHERE up.colleague_id = ?
            ORDER BY p.name ASC
            """,
            (colleague_id,),
        ).fetchall()

    return [{"id": row["id"], "name": row["name"], "description": row["description"] or ""} for row in rows]
