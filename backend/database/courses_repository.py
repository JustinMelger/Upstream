from __future__ import annotations

from backend.database.db import SQLiteDatabase
from backend.database.models import CourseRecord


class SQLiteCoursesRepository:
    """SQLite implementation of courses persistence."""

    def __init__(self, db: SQLiteDatabase):
        """Initialize the repository.

        Args:
            db: SQLite database client.
        """
        self._db = db

    def list_courses(
        self,
        query: str | None,
        provider: str | None,
        category: str | None,
        level: str | None,
    ) -> list[CourseRecord]:
        """List courses with optional filters.

        Args:
            query: Search query.
            provider: Provider filter.
            category: Category filter.
            level: Level filter.

        Returns:
            List of course records.
        """
        sql = "SELECT id, title, provider, category, level, duration_hours, url, created_at FROM courses"
        clauses: list[str] = []
        params: list[str] = []

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

        with self._db.get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        return [
            CourseRecord(
                id=row["id"],
                title=row["title"] or "",
                provider=row["provider"],
                category=row["category"],
                level=row["level"],
                duration_hours=row["duration_hours"],
                url=row["url"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_course_by_id(self, course_id: int) -> CourseRecord | None:
        """Fetch a course by ID.

        Args:
            course_id: Course ID.

        Returns:
            Course record or None.
        """
        with self._db.get_conn() as conn:
            row = conn.execute(
                "SELECT id, title, provider, category, level, duration_hours, url, created_at FROM courses WHERE id = ?",
                (course_id,),
            ).fetchone()
        if not row:
            return None
        return CourseRecord(
            id=row["id"],
            title=row["title"] or "",
            provider=row["provider"],
            category=row["category"],
            level=row["level"],
            duration_hours=row["duration_hours"],
            url=row["url"],
            created_at=row["created_at"],
        )

    def create_course(
        self,
        title: str,
        provider: str | None,
        category: str | None,
        level: str | None,
        duration_hours: float | None,
        url: str | None,
        created_at: str,
    ) -> int:
        """Create a course.

        Args:
            title: Course title.
            provider: Provider name.
            category: Category name.
            level: Level value.
            duration_hours: Duration in hours.
            url: Course URL.
            created_at: ISO timestamp.

        Returns:
            Created course ID.
        """
        with self._db.get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO courses (title, provider, category, level, duration_hours, url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (title, provider, category, level, duration_hours, url, created_at),
            )
            conn.commit()
            return int(cur.lastrowid)

    def update_course(
        self,
        course_id: int,
        title: str,
        provider: str | None,
        category: str | None,
        level: str | None,
        duration_hours: float | None,
        url: str | None,
    ) -> int:
        """Update a course.

        Args:
            course_id: Course ID.
            title: Updated title.
            provider: Updated provider.
            category: Updated category.
            level: Updated level.
            duration_hours: Updated duration.
            url: Updated URL.

        Returns:
            Number of rows updated.
        """
        with self._db.get_conn() as conn:
            cur = conn.execute(
                """
                UPDATE courses
                SET title = ?, provider = ?, category = ?, level = ?, duration_hours = ?, url = ?
                WHERE id = ?
                """,
                (title, provider, category, level, duration_hours, url, course_id),
            )
            conn.commit()
            return cur.rowcount

    def delete_course(self, course_id: int) -> int:
        """Delete a course by ID.

        Args:
            course_id: Course ID.

        Returns:
            Number of rows deleted.
        """
        with self._db.get_conn() as conn:
            cur = conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
            conn.commit()
            return cur.rowcount
