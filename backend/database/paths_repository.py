from __future__ import annotations

from backend.database.db import SQLiteDatabase
from backend.database.models import PathCourseRecord, PathRecord


class SQLitePathsRepository:
    """SQLite implementation of paths persistence."""

    def __init__(self, db: SQLiteDatabase):
        """Initialize the repository.

        Args:
            db: SQLite database client.
        """
        self._db = db

    def list_paths(self) -> list[PathRecord]:
        """List all learning paths.

        Returns:
            List of path records.
        """
        with self._db.get_conn() as conn:
            rows = conn.execute("SELECT id, name, description FROM paths ORDER BY name ASC").fetchall()
        return [PathRecord(id=row["id"], name=row["name"], description=row["description"]) for row in rows]

    def get_path(self, path_id: int) -> tuple[PathRecord, list[PathCourseRecord]] | None:
        """Fetch a path and its courses by ID.

        Args:
            path_id: Path ID.

        Returns:
            Tuple of (path record, path course records) or None.
        """
        with self._db.get_conn() as conn:
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

        return (
            PathRecord(id=path["id"], name=path["name"], description=path["description"]),
            [
                PathCourseRecord(
                    id=row["id"],
                    title=row["title"] or "",
                    provider=row["provider"],
                    category=row["category"],
                    level=row["level"],
                    duration_hours=row["duration_hours"],
                    url=row["url"],
                    position=row["position"],
                )
                for row in courses
            ],
        )

    def create_path(self, name: str, description: str | None) -> int:
        """Create a path.

        Args:
            name: Path name.
            description: Optional description.

        Returns:
            Created path ID.
        """
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO paths (name, description) VALUES (?, ?)",
                (name, description),
            )
            conn.commit()
            return int(cur.lastrowid)

    def create_path_with_courses(self, name: str, description: str | None, course_ids: list[int]) -> int:
        """Create a path and set its ordered courses atomically."""
        with self._db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO paths (name, description) VALUES (?, ?)",
                (name, description),
            )
            path_id = int(cur.lastrowid)
            conn.execute("DELETE FROM path_courses WHERE path_id = ?", (path_id,))
            if course_ids:
                conn.executemany(
                    "INSERT OR IGNORE INTO path_courses (path_id, course_id, position) VALUES (?, ?, ?)",
                    [(path_id, int(course_id), idx) for idx, course_id in enumerate(course_ids)],
                )
            return path_id

    def path_name_exists(self, name: str) -> bool:
        """Check if a path name exists (case-insensitive)."""
        with self._db.get_conn() as conn:
            existing = conn.execute("SELECT 1 FROM paths WHERE lower(name) = lower(?) LIMIT 1", (name,)).fetchone()
        return existing is not None

    def path_name_exists_for_other_id(self, path_id: int, name: str) -> bool:
        """Check if a path name exists for a different path."""
        with self._db.get_conn() as conn:
            existing = conn.execute(
                "SELECT 1 FROM paths WHERE lower(name) = lower(?) AND id != ? LIMIT 1",
                (name, path_id),
            ).fetchone()
        return existing is not None

    def set_path_courses(self, path_id: int, course_ids: list[int]) -> None:
        """Replace a path's courses with an ordered list."""
        if not course_ids:
            return
        with self._db.get_conn() as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO path_courses (path_id, course_id, position) VALUES (?, ?, ?)",
                [(path_id, int(course_id), idx) for idx, course_id in enumerate(course_ids)],
            )
            conn.commit()

    def delete_path_courses(self, path_id: int) -> None:
        """Delete all courses for a path."""
        with self._db.get_conn() as conn:
            conn.execute("DELETE FROM path_courses WHERE path_id = ?", (path_id,))
            conn.commit()

    def update_path(self, path_id: int, name: str, description: str | None) -> int:
        """Update path metadata."""
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "UPDATE paths SET name = ?, description = ? WHERE id = ?",
                (name, description, path_id),
            )
            conn.commit()
            return cur.rowcount

    def update_path_with_courses(self, path_id: int, name: str, description: str | None, course_ids: list[int]) -> int:
        """Update a path and reset its ordered courses atomically."""
        with self._db.transaction() as conn:
            cur = conn.execute(
                "UPDATE paths SET name = ?, description = ? WHERE id = ?",
                (name, description, path_id),
            )
            conn.execute("DELETE FROM path_courses WHERE path_id = ?", (path_id,))
            if course_ids:
                conn.executemany(
                    "INSERT OR IGNORE INTO path_courses (path_id, course_id, position) VALUES (?, ?, ?)",
                    [(path_id, int(course_id), idx) for idx, course_id in enumerate(course_ids)],
                )
            return cur.rowcount

    def delete_path(self, path_id: int) -> int:
        """Delete a path by ID."""
        with self._db.get_conn() as conn:
            cur = conn.execute("DELETE FROM paths WHERE id = ?", (path_id,))
            conn.commit()
            return cur.rowcount

    def delete_path_with_courses(self, path_id: int) -> int:
        """Delete a path and its course mappings atomically."""
        with self._db.transaction() as conn:
            conn.execute("DELETE FROM path_courses WHERE path_id = ?", (path_id,))
            cur = conn.execute("DELETE FROM paths WHERE id = ?", (path_id,))
            return cur.rowcount
