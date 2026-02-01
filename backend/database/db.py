import csv
import sqlite3
from pathlib import Path
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
  url TEXT
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
  UNIQUE(path_id, course_id)
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def seed_courses_from_csv(csv_path: Path) -> None:
    if not csv_path.exists():
        return

    with get_conn() as conn:
        existing = conn.execute("SELECT 1 FROM courses LIMIT 1").fetchone()
        if existing:
            return

        rows = _read_csv(csv_path)
        if not rows:
            return

        conn.executemany(
            """
            INSERT INTO courses (title, provider, category, level, duration_hours, url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row.get("title"),
                    row.get("provider"),
                    row.get("category"),
                    row.get("level"),
                    _parse_float(row.get("duration_hours")),
                    row.get("url"),
                )
                for row in rows
                if (row.get("title") or "").strip()
            ],
        )
        conn.commit()


def _read_csv(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [row for row in reader]


def _parse_float(value):
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None
