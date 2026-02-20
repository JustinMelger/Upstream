"""Pure filter normalization/query helpers for Courses page."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CoursesFilterValues:
    """Normalized filter values consumed by reducers and UI glue."""

    scope: str
    search: str
    provider: str
    category: str
    level: str
    status: str
    sort: str


def normalize_courses_filter_values(
    *,
    scope_value: str,
    search_value: str,
    provider_value: str,
    category_value: str,
    level_value: str,
    status_value: str,
    sort_value: str,
) -> CoursesFilterValues:
    """Normalize raw filter control values into stable reducer inputs."""
    return CoursesFilterValues(
        scope=str(scope_value or "all"),
        search=str(search_value or "").strip().lower(),
        provider=str(provider_value or "").strip().lower(),
        category=str(category_value or "").strip().lower(),
        level=str(level_value or "").strip().lower(),
        status=str(status_value or "").strip(),
        sort=str(sort_value or "").strip(),
    )


def build_list_query_params(
    *,
    search_value: str,
    provider_value: str,
    category_value: str,
    level_value: str,
) -> dict[str, str]:
    """Build `/courses` list query params from non-empty filter fields."""
    params: dict[str, str] = {}
    search = str(search_value or "").strip()
    provider = str(provider_value or "").strip()
    category = str(category_value or "").strip()
    level = str(level_value or "").strip()
    if search:
        params["q"] = search
    if provider:
        params["provider"] = provider
    if category:
        params["category"] = category
    if level:
        params["level"] = level
    return params
