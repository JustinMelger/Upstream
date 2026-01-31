from typing import Dict, List, Optional

from backend.database.db import get_conn


def list_courses(
    query: Optional[str] = None,
    provider: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
) -> List[Dict[str, str]]:
    sql = "SELECT id, title, provider, category, level, duration_hours, url FROM courses"
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
        }
        for row in rows
    ]
