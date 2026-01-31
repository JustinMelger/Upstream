import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from backend.core.config import settings


TRACKING_FIELDS = ["colleague_id", "course_id", "status", "updated_at"]
STATUS_VALUES = {"interested", "in_progress", "completed"}


def _load_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append({key: (row.get(key) or "").strip() for key in TRACKING_FIELDS})
        return rows


def _write_rows(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRACKING_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def list_tracking(colleague_id: Optional[str] = None) -> List[Dict[str, str]]:
    path = Path(settings.tracking_csv)
    rows = _load_rows(path)
    if colleague_id:
        rows = [r for r in rows if r["colleague_id"] == colleague_id]
    return rows


def upsert_tracking(colleague_id: str, course_id: int, status: str) -> Dict[str, str]:
    if status not in STATUS_VALUES:
        raise ValueError("invalid_status")

    path = Path(settings.tracking_csv)
    rows = _load_rows(path)
    now = datetime.now(timezone.utc).isoformat()
    course_id_str = str(course_id)

    updated = False
    for row in rows:
        if row["colleague_id"] == colleague_id and row["course_id"] == course_id_str:
            row["status"] = status
            row["updated_at"] = now
            updated = True
            break

    if not updated:
        rows.append(
            {
                "colleague_id": colleague_id,
                "course_id": course_id_str,
                "status": status,
                "updated_at": now,
            }
        )

    _write_rows(path, rows)
    return {
        "colleague_id": colleague_id,
        "course_id": course_id_str,
        "status": status,
        "updated_at": now,
    }
