import csv
from pathlib import Path
from typing import Dict, List, Optional

from backend.core.config import settings


COURSE_FIELDS = ["title", "provider", "category", "level", "duration_hours", "url"]


def _load_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append({key: (row.get(key) or "").strip() for key in COURSE_FIELDS})
        return rows


def list_courses(
    query: Optional[str] = None,
    provider: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
) -> List[Dict[str, str]]:
    path = Path(settings.courses_csv)
    rows = _load_rows(path)

    with_ids = []
    for idx, row in enumerate(rows, start=1):
        row_with_id = dict(row)
        row_with_id["id"] = idx
        with_ids.append(row_with_id)

    rows = with_ids

    if query:
        needle = query.lower()
        rows = [
            r
            for r in rows
            if needle
            in " ".join([r["title"], r["provider"], r["category"]]).lower()
        ]

    if provider:
        rows = [r for r in rows if r["provider"] == provider]
    if category:
        rows = [r for r in rows if r["category"] == category]
    if level:
        rows = [r for r in rows if r["level"] == level]

    return rows
