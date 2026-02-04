from typing import Dict, List, Optional

from backend.database.db import get_conn


def list_paths() -> List[Dict[str, str]]:
    """List all learning paths.

    Returns:
        list[dict]: Path list.
    """
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name, description FROM paths ORDER BY name ASC").fetchall()
    return [{"id": row["id"], "name": row["name"], "description": row["description"] or ""} for row in rows]


def get_path(path_id: int) -> Optional[Dict[str, str]]:
    """Fetch a path and its courses by ID.

    Args:
        path_id: Path ID.

    Returns:
        dict | None: Path payload or None.
    """
    with get_conn() as conn:
        path = conn.execute("SELECT id, name, description FROM paths WHERE id = ?", (path_id,)).fetchone()
        if not path:
            return None
        courses = conn.execute(
            """
            SELECT c.id, c.title, c.provider, c.category, c.level, c.duration_hours, c.url, pc.position
            FROM path_courses pc
            JOIN courses c ON c.id = pc.course_id
            WHERE pc.path_id = ?
            ORDER BY COALESCE(pc.position, 9999) ASC, c.title ASC
            """,
            (path_id,),
        ).fetchall()

    return {
        "id": path["id"],
        "name": path["name"],
        "description": path["description"] or "",
        "courses": [
            {
                "id": row["id"],
                "title": row["title"] or "",
                "provider": row["provider"] or "",
                "category": row["category"] or "",
                "level": row["level"] or "",
                "duration_hours": row["duration_hours"],
                "url": row["url"] or "",
            }
            for row in courses
        ],
    }


def create_path(payload: dict) -> Dict[str, str]:
    """Create a learning path with ordered courses.

    Args:
        payload: Path payload with course_ids.

    Returns:
        dict: Created path.
    """
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("missing_name")
    description = (payload.get("description") or "").strip() or None
    course_ids = payload.get("course_ids") or []

    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM paths WHERE lower(name) = lower(?)", (name,)).fetchone()
        if existing:
            raise ValueError("duplicate_name")

        cur = conn.execute(
            "INSERT INTO paths (name, description) VALUES (?, ?)",
            (name, description),
        )
        path_id = cur.lastrowid

        if course_ids:
            conn.executemany(
                "INSERT OR IGNORE INTO path_courses (path_id, course_id, position) VALUES (?, ?, ?)",
                [(path_id, int(cid), idx) for idx, cid in enumerate(course_ids)],
            )
        conn.commit()

    return get_path(path_id) or {"error": "not_found"}


def delete_path(path_id: int) -> bool:
    """Delete a learning path by ID.

    Args:
        path_id: Path ID.

    Returns:
        bool: True if deleted.
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM path_courses WHERE path_id = ?", (path_id,))
        cur = conn.execute("DELETE FROM paths WHERE id = ?", (path_id,))
        conn.commit()
    return cur.rowcount > 0


def update_path(path_id: int, payload: dict) -> Dict[str, str]:
    """Update a learning path and its course ordering.

    Args:
        path_id: Path ID.
        payload: Path updates and course_ids order.

    Returns:
        dict: Updated path.
    """
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("missing_name")
    description = (payload.get("description") or "").strip() or None
    course_ids = payload.get("course_ids") or []

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM paths WHERE lower(name) = lower(?) AND id != ?",
            (name, path_id),
        ).fetchone()
        if existing:
            raise ValueError("duplicate_name")

        conn.execute(
            "UPDATE paths SET name = ?, description = ? WHERE id = ?",
            (name, description, path_id),
        )
        conn.execute("DELETE FROM path_courses WHERE path_id = ?", (path_id,))
        if course_ids:
            conn.executemany(
                "INSERT OR IGNORE INTO path_courses (path_id, course_id, position) VALUES (?, ?, ?)",
                [(path_id, int(cid), idx) for idx, cid in enumerate(course_ids)],
            )
        conn.commit()

    return get_path(path_id) or {"error": "not_found"}
