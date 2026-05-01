"""Pure filter normalization/query helpers for Paths page."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PathsFilterValues(BaseModel):
    """Normalized filter values consumed by reducers and UI glue."""

    model_config = ConfigDict(frozen=True)

    scope: str
    search: str
    status: str
    sort: str


def normalize_paths_filter_values(
    *,
    scope_value: str,
    search_value: str,
    status_value: str,
    sort_value: str,
) -> PathsFilterValues:
    """Normalize raw filter control values into stable reducer inputs."""
    return PathsFilterValues(
        scope=str(scope_value or "all").strip(),
        search=str(search_value or "").strip().lower(),
        status=str(status_value or "").strip(),
        sort=str(sort_value or "").strip(),
    )


def build_paths_list_query_params(*, search_value: str) -> dict[str, str]:
    """Build optional list query params for future server-side filtering."""
    params: dict[str, str] = {}
    search = str(search_value or "").strip()
    if search:
        params["q"] = search
    return params
