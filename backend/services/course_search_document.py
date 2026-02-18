from __future__ import annotations

from collections.abc import Sequence
import re

from backend.database.models import CourseRecord


_WS_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def build_course_search_document(
    *,
    course: CourseRecord,
    review_texts: Sequence[str] | None = None,
    recommendation_count: int | None = None,
    recommendation_notes: Sequence[str] | None = None,
    recommended_by: Sequence[str] | None = None,
) -> str:
    """Build a normalized search document for AI/search workflows.

    The document combines course metadata with optional review text snippets.
    """
    parts: list[str] = []
    for value in (
        course.title,
        course.description,
        course.learning_outcomes or "",
        course.prerequisites or "",
        course.language or "",
        course.provider or "",
        course.category or "",
        course.level or "",
    ):
        normalized = _normalize(str(value or ""))
        if normalized:
            parts.append(normalized)

    for text in list(review_texts or []):
        normalized = _normalize(str(text or ""))
        if normalized:
            parts.append(normalized)

    rec_count = int(recommendation_count or 0)
    if rec_count > 0:
        parts.append(f"recommended {rec_count} time{'s' if rec_count != 1 else ''}")

    rec_by = [_normalize(str(name or "")) for name in list(recommended_by or [])]
    rec_by = [name for name in rec_by if name]
    if rec_by:
        parts.append(f"recommended_by {' '.join(rec_by)}")

    for note in list(recommendation_notes or []):
        normalized = _normalize(str(note or ""))
        if normalized:
            parts.append(normalized)

    return "\n".join(parts)
