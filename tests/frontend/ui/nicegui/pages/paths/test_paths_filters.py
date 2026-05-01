from __future__ import annotations

from frontend.ui.nicegui.domains.paths.filters import build_paths_list_query_params, normalize_paths_filter_values


def test_normalize_paths_filter_values_normalizes_search_and_fields() -> None:
    values = normalize_paths_filter_values(
        scope_value="",
        search_value="  API Fundamentals ",
        status_value="tracked",
        sort_value="name_az",
    )
    assert values.scope == "all"
    assert values.search == "api fundamentals"
    assert values.status == "tracked"
    assert values.sort == "name_az"


def test_build_paths_list_query_params_only_includes_non_empty_search() -> None:
    assert build_paths_list_query_params(search_value="  fastapi ") == {"q": "fastapi"}
    assert build_paths_list_query_params(search_value=" ") == {}
