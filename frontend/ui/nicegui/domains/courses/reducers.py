"""Pure reducer-style helpers for Courses page transitions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable


_TRACKING_STATES = {"interested", "in_progress", "completed"}


def tracking_status_key(*, tracking_by_course_id: dict[int, dict[str, Any]], course_id: int) -> str:
    """Return normalized tracking status key for faceting/sorting."""
    tracked = tracking_by_course_id.get(int(course_id))
    value = str((tracked or {}).get("status") or "").strip()
    return value if value in _TRACKING_STATES else "not_tracked"


def _matches_optional_course_field(
    *,
    course: dict[str, Any],
    field: str,
    expected: str,
    ignore: str,
    ignore_key: str,
) -> bool:
    if ignore == ignore_key or not expected:
        return True
    return expected == str(course.get(field) or "").strip().lower()


def _course_matches(
    course: dict[str, Any],
    *,
    tracking_by_course_id: dict[int, dict[str, Any]],
    scope_value: str,
    needle: str,
    provider_value: str,
    category_value: str,
    level_value: str,
    status_value: str,
    ignore: str = "",
) -> bool:
    if ignore != "scope" and scope_value == "tracked":
        cid = int(course.get("id") or 0)
        if cid <= 0 or cid not in tracking_by_course_id:
            return False
    if ignore != "needle" and needle:
        if needle not in str(course.get("title") or "").lower() and needle not in str(course.get("description") or "").lower():
            return False
    if not (
        _matches_optional_course_field(
            course=course,
            field="provider",
            expected=provider_value,
            ignore=ignore,
            ignore_key="provider",
        )
        and _matches_optional_course_field(
            course=course,
            field="category",
            expected=category_value,
            ignore=ignore,
            ignore_key="category",
        )
        and _matches_optional_course_field(
            course=course,
            field="level",
            expected=level_value,
            ignore=ignore,
            ignore_key="level",
        )
    ):
        return False
    if ignore != "status" and status_value:
        cid = int(course.get("id") or 0)
        if status_value == "not_tracked":
            if cid in tracking_by_course_id:
                return False
        else:
            if tracking_status_key(tracking_by_course_id=tracking_by_course_id, course_id=cid) != status_value:
                return False
    return True


def compute_facet_counts(
    *,
    courses: list[dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
    scope_value: str,
    needle: str,
    provider_value: str,
    category_value: str,
    level_value: str,
    status_value: str,
) -> tuple[dict[str, int], dict[str, int], dict[str, int], dict[str, int]]:
    """Compute provider/category/level/status counts (excluding current facet)."""

    def _count_values(*, ignore: str, field: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for course in courses:
            if not _course_matches(
                course,
                tracking_by_course_id=tracking_by_course_id,
                scope_value=scope_value,
                needle=needle,
                provider_value=provider_value,
                category_value=category_value,
                level_value=level_value,
                status_value=status_value,
                ignore=ignore,
            ):
                continue
            value = str(course.get(field) or "").strip()
            if not value:
                continue
            counts[value] = int(counts.get(value, 0)) + 1
        return counts

    provider_counts = _count_values(ignore="provider", field="provider")
    category_counts = _count_values(ignore="category", field="category")
    level_counts = _count_values(ignore="level", field="level")

    status_counts: dict[str, int] = {"not_tracked": 0, "interested": 0, "in_progress": 0, "completed": 0}
    for course in courses:
        if not _course_matches(
            course,
            tracking_by_course_id=tracking_by_course_id,
            scope_value=scope_value,
            needle=needle,
            provider_value=provider_value,
            category_value=category_value,
            level_value=level_value,
            status_value=status_value,
            ignore="status",
        ):
            continue
        cid = int(course.get("id") or 0)
        key = tracking_status_key(tracking_by_course_id=tracking_by_course_id, course_id=cid)
        status_counts[key] = int(status_counts.get(key, 0)) + 1

    return provider_counts, category_counts, level_counts, status_counts


def build_count_options(*, any_label: str, counts: dict[str, int]) -> dict[str, str]:
    """Build sorted select options with counts for provider/category/level facets."""
    sorted_items = sorted(counts.items(), key=lambda kv: (-int(kv[1]), str(kv[0]).lower()))
    return {"": any_label, **{key: f"{key} ({count})" for key, count in sorted_items}}


def build_status_options(*, status_counts: dict[str, int]) -> dict[str, str]:
    """Build status facet options with counts."""
    return {
        "": "Any status",
        "not_tracked": f"Not tracked ({status_counts.get('not_tracked', 0)})",
        "interested": f"Interested ({status_counts.get('interested', 0)})",
        "in_progress": f"In progress ({status_counts.get('in_progress', 0)})",
        "completed": f"Completed ({status_counts.get('completed', 0)})",
    }


def filter_courses(
    *,
    courses: list[dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
    scope_value: str,
    needle: str,
    provider_value: str,
    category_value: str,
    level_value: str,
    status_value: str,
) -> list[dict[str, Any]]:
    """Apply list filters and return matching courses."""
    return [
        course
        for course in courses
        if _course_matches(
            course,
            tracking_by_course_id=tracking_by_course_id,
            scope_value=scope_value,
            needle=needle,
            provider_value=provider_value,
            category_value=category_value,
            level_value=level_value,
            status_value=status_value,
        )
    ]


def sort_courses(
    *,
    courses: list[dict[str, Any]],
    sort_value: str,
    review_summary_by_course_id: dict[int, dict[str, Any]],
    parse_iso_datetime: Callable[[Any], datetime | None],
) -> list[dict[str, Any]]:
    """Sort filtered courses according to selected sort value."""
    shown = list(courses)
    if not sort_value:
        return shown
    if sort_value == "title_az":
        return sorted(shown, key=lambda c: str(c.get("title") or "").strip().lower())
    if sort_value == "newest":

        def _created_key(course: dict[str, Any]) -> tuple[datetime, int]:
            dt = parse_iso_datetime(course.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)
            return (dt, int(course.get("id") or 0))

        return sorted(shown, key=_created_key, reverse=True)
    if sort_value == "top_rated":

        def _rating_key(course: dict[str, Any]) -> tuple[float, int, str]:
            cid = int(course.get("id") or 0)
            summary = review_summary_by_course_id.get(cid) or {}
            try:
                avg = float(summary.get("avg_rating") or 0.0)
            except (TypeError, ValueError):
                avg = 0.0
            try:
                count = int(summary.get("review_count") or 0)
            except (TypeError, ValueError):
                count = 0
            title = str(course.get("title") or "").strip().lower()
            return (avg, count, title)

        return sorted(shown, key=_rating_key, reverse=True)
    if sort_value == "most_reviewed":

        def _count_key(course: dict[str, Any]) -> tuple[int, float, str]:
            cid = int(course.get("id") or 0)
            summary = review_summary_by_course_id.get(cid) or {}
            try:
                count = int(summary.get("review_count") or 0)
            except (TypeError, ValueError):
                count = 0
            try:
                avg = float(summary.get("avg_rating") or 0.0)
            except (TypeError, ValueError):
                avg = 0.0
            title = str(course.get("title") or "").strip().lower()
            return (count, avg, title)

        return sorted(shown, key=_count_key, reverse=True)
    return shown
