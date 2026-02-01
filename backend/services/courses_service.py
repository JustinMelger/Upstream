from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.database.db import get_conn


def list_courses(
    query: Optional[str] = None,
    provider: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
) -> List[Dict[str, str]]:
    sql = "SELECT id, title, provider, category, level, duration_hours, url, created_at FROM courses"
    clauses = []
    params: List[str] = []

    if query:
        clauses.append("(lower(title) LIKE ? OR lower(provider) LIKE ? OR lower(category) LIKE ?)")
        like = f"%{query.lower()}%"
        params.extend([like, like, like])
    if provider:
        clauses.append("provider = ?")
        params.append(provider)
    if category:
        clauses.append("category = ?")
        params.append(category)
    if level:
        clauses.append("level = ?")
        params.append(level)

    if clauses:
        sql += " WHERE " + " AND ".join(clauses)

    sql += " ORDER BY title ASC"

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [
        {
            "id": row["id"],
            "title": row["title"] or "",
            "provider": row["provider"] or "",
            "category": row["category"] or "",
            "level": row["level"] or "",
            "duration_hours": row["duration_hours"],
            "url": row["url"] or "",
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def get_course_by_id(course_id: int) -> Optional[Dict[str, str]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, title, provider, category, level, duration_hours, url, created_at FROM courses WHERE id = ?",
            (course_id,),
        ).fetchone()

    if not row:
        return None

    return {
        "id": row["id"],
        "title": row["title"] or "",
        "provider": row["provider"] or "",
        "category": row["category"] or "",
        "level": row["level"] or "",
        "duration_hours": row["duration_hours"],
        "url": row["url"] or "",
        "created_at": row["created_at"],
    }


def create_course(payload: dict) -> Dict[str, str]:
    title = (payload.get("title") or "").strip()
    if not title:
        raise ValueError("missing_title")

    provider = (payload.get("provider") or "").strip() or None
    category = (payload.get("category") or "").strip() or None
    level = (payload.get("level") or "").strip() or None
    url = (payload.get("url") or "").strip() or None
    duration_hours = _parse_float(payload.get("duration_hours"))
    created_at = datetime.now(timezone.utc).isoformat()

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO courses (title, provider, category, level, duration_hours, url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (title, provider, category, level, duration_hours, url, created_at),
        )
        conn.commit()
        course_id = cur.lastrowid

    return get_course_by_id(course_id) or {"error": "not_found"}


def update_course(course_id: int, payload: dict) -> Optional[Dict[str, str]]:
    existing = get_course_by_id(course_id)
    if not existing:
        return None

    title = (payload.get("title") or existing["title"]).strip()
    provider = (payload.get("provider") or existing["provider"]).strip() or None
    category = (payload.get("category") or existing["category"]).strip() or None
    level = (payload.get("level") or existing["level"]).strip() or None
    url = (payload.get("url") or existing["url"]).strip() or None
    duration_hours = _parse_float(payload.get("duration_hours"))
    if duration_hours is None:
        duration_hours = existing["duration_hours"]

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE courses
            SET title = ?, provider = ?, category = ?, level = ?, duration_hours = ?, url = ?
            WHERE id = ?
            """,
            (title, provider, category, level, duration_hours, url, course_id),
        )
        conn.commit()

    return get_course_by_id(course_id)


def delete_course(course_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        conn.commit()
    return cur.rowcount > 0


def _parse_float(value):
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None
