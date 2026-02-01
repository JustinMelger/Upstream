from typing import Dict, List, Optional

from backend.database.db import get_conn


def list_paths() -> List[Dict[str, str]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name, description FROM paths ORDER BY name ASC").fetchall()
    return [{"id": row["id"], "name": row["name"], "description": row["description"] or ""} for row in rows]


def get_path(path_id: int) -> Optional[Dict[str, str]]:
    with get_conn() as conn:
        path = conn.execute("SELECT id, name, description FROM paths WHERE id = ?", (path_id,)).fetchone()
        if not path:
            return None
        courses = conn.execute(
            """
            SELECT c.id, c.title, c.provider, c.category, c.level, c.duration_hours, c.url
            FROM path_courses pc
            JOIN courses c ON c.id = pc.course_id
            WHERE pc.path_id = ?
            ORDER BY c.title ASC
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
                "INSERT OR IGNORE INTO path_courses (path_id, course_id) VALUES (?, ?)",
                [(path_id, int(cid)) for cid in course_ids],
            )
        conn.commit()

    return get_path(path_id) or {"error": "not_found"}


def delete_path(path_id: int) -> bool:
    with get_conn() as conn:
        conn.execute("DELETE FROM path_courses WHERE path_id = ?", (path_id,))
        cur = conn.execute("DELETE FROM paths WHERE id = ?", (path_id,))
        conn.commit()
    return cur.rowcount > 0
