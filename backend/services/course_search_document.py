from __future__ import annotations

from collections.abc import Sequence
import re

from backend.database.models import CourseRecord


_WS_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def _append_normalized(parts: list[str], value: object) -> None:
    normalized = _normalize(str(value or ""))
    if normalized:
        parts.append(normalized)


def _append_recommendation_count(parts: list[str], recommendation_count: int | None) -> None:
    rec_count = int(recommendation_count or 0)
    if rec_count > 0:
        parts.append(f"recommended {rec_count} time{'s' if rec_count != 1 else ''}")


def _append_recommended_by(parts: list[str], recommended_by: Sequence[str] | None) -> None:
    names = [_normalize(str(name or "")) for name in list(recommended_by or [])]
    names = [name for name in names if name]
    if names:
        parts.append(f"recommended_by {' '.join(names)}")


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
        _append_normalized(parts, value)

    for text in list(review_texts or []):
        _append_normalized(parts, text)

    _append_recommendation_count(parts, recommendation_count)
    _append_recommended_by(parts, recommended_by)

    for note in list(recommendation_notes or []):
        _append_normalized(parts, note)

    return "\n".join(parts)
