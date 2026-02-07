from __future__ import annotations

from contextlib import contextmanager
import csv
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Iterable

from backend.core.config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  provider TEXT,
  category TEXT,
  level TEXT,
  duration_hours REAL,
  url TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS tracking (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  colleague_id TEXT NOT NULL,
  course_id INTEGER NOT NULL,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(colleague_id, course_id)
);

CREATE TABLE IF NOT EXISTS paths (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  description TEXT
);

CREATE TABLE IF NOT EXISTS path_courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path_id INTEGER NOT NULL,
  course_id INTEGER NOT NULL,
  position INTEGER,
  UNIQUE(path_id, course_id)
);

CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  colleague_id TEXT NOT NULL,
  token_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  last_seen TEXT NOT NULL,
  expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_login_at TEXT,
  disabled INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_paths (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  colleague_id TEXT NOT NULL,
  path_id INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT,
  status TEXT,
  UNIQUE(colleague_id, path_id)
);
"""


class SQLiteDatabase:
    """SQLite database wrapper."""

    def __init__(self, *, db_path: str):
        """Initialize the database client.

        Args:
            db_path: Filesystem path to the SQLite database.
        """
        self.db_path = db_path

    def get_conn(self) -> sqlite3.Connection:
        """Create a database connection.

        Returns:
            sqlite3.Connection: Connection with row factory configured.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def transaction(self) -> Iterable[sqlite3.Connection]:
        """Open a connection and run statements in a transaction.

        This is useful for multi-table operations that must be atomic.

        Yields:
            sqlite3.Connection: An open connection inside a transaction.
        """
        conn = self.get_conn()
        try:
            conn.execute("BEGIN")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        """Initialize database schema and ensure columns/indexes exist."""
        with self.get_conn() as conn:
            conn.executescript(SCHEMA)
            self._ensure_column(conn, "courses", "created_at", "TEXT")
            self._ensure_column(conn, "path_courses", "position", "INTEGER")
            self._ensure_column(conn, "sessions", "expires_at", "TEXT")
            self._ensure_column(conn, "sessions", "last_seen", "TEXT")
            self._ensure_column(conn, "sessions", "token_hash", "TEXT")
            self._ensure_column(conn, "sessions", "colleague_id", "TEXT")
            self._ensure_column(conn, "sessions", "created_at", "TEXT")
            self._ensure_column(conn, "users", "username", "TEXT")
            self._ensure_column(conn, "users", "password_hash", "TEXT")
            self._ensure_column(conn, "users", "role", "TEXT")
            self._ensure_column(conn, "users", "created_at", "TEXT")
            self._ensure_column(conn, "users", "updated_at", "TEXT")
            self._ensure_column(conn, "users", "last_login_at", "TEXT")
            self._ensure_column(conn, "users", "disabled", "INTEGER")
            self._ensure_column(conn, "user_paths", "status", "TEXT")
            self._ensure_column(conn, "user_paths", "updated_at", "TEXT")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions (token_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_colleague ON sessions (colleague_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")
            conn.commit()

    def seed_courses_from_csv(self, csv_path: Path) -> None:
        """Seed courses from a CSV file if the table is empty.

        Args:
            csv_path: Path to the CSV seed file.
        """
        if not csv_path.exists():
            return

        with self.get_conn() as conn:
            existing = conn.execute("SELECT 1 FROM courses LIMIT 1").fetchone()
            if existing:
                return

            rows = self._read_csv(csv_path)
            if not rows:
                return

            now = datetime.now(timezone.utc).isoformat()

            conn.executemany(
                """
                INSERT INTO courses (title, provider, category, level, duration_hours, url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row.get("title"),
                        row.get("provider"),
                        row.get("category"),
                        row.get("level"),
                        self._parse_float(row.get("duration_hours")),
                        row.get("url"),
                        now,
                    )
                    for row in rows
                    if (row.get("title") or "").strip()
                ],
            )
            conn.commit()

    @staticmethod
    def _read_csv(path: Path) -> Iterable[dict]:
        """Read a CSV file into a list of row dicts."""
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            return [row for row in reader]

    @staticmethod
    def _parse_float(value):
        """Parse a float value or return None."""
        try:
            return float(value) if value not in (None, "") else None
        except ValueError:
            return None

    @staticmethod
    def _ensure_column(conn: sqlite3.Connection, table: str, column: str, col_type: str) -> None:
        """Add a column to a table if it doesn't exist."""
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        columns = {row["name"] for row in rows}
        if column not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            conn.commit()


database = SQLiteDatabase(db_path=settings.db_path)


def get_conn() -> sqlite3.Connection:
    """Create a database connection."""
    return database.get_conn()


def init_db() -> None:
    """Initialize database schema and ensure columns/indexes exist."""
    database.init_db()


def seed_courses_from_csv(csv_path: Path) -> None:
    """Seed courses from a CSV file if the table is empty."""
    database.seed_courses_from_csv(csv_path)
