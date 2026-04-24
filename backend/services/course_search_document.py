from __future__ import annotations

import re

from backend.database.models import CourseRecord


_WS_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def _append_normalized(parts: list[str], value: object) -> None:
    normalized = _normalize(str(value or ""))
    if normalized:
        parts.append(normalized)


def build_course_search_document(
    *,
    course: CourseRecord,
    review_texts: list[str] | tuple[str, ...] | None = None,
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

    return "\n".join(parts)
