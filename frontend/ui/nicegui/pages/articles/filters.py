"""Pure filter normalization/query helpers for Articles page."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ArticlesFilterValues:
    """Normalized filter values consumed by reducers and UI glue."""

    search: str
    tag: str
    author: str
    sort: str


def normalize_articles_filter_values(
    *,
    search_value: str,
    tag_value: str,
    author_value: str,
    sort_value: str,
) -> ArticlesFilterValues:
    """Normalize raw filter control values into stable reducer inputs."""
    return ArticlesFilterValues(
        search=str(search_value or "").strip(),
        tag=str(tag_value or "").strip(),
        author=str(author_value or "").strip(),
        sort=str(sort_value or "").strip(),
    )


def build_articles_list_query_params(*, search_value: str) -> dict[str, str]:
    """Build optional list query params for future server-side filtering."""
    params: dict[str, str] = {}
    search = str(search_value or "").strip()
    if search:
        params["q"] = search
    return params
