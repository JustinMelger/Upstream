from __future__ import annotations

from frontend.ui.nicegui.domains.courses.filters import build_list_query_params, normalize_courses_filter_values


def test_normalize_courses_filter_values_normalizes_search_and_facets() -> None:
    values = normalize_courses_filter_values(
        scope_value="",
        search_value="  FastAPI  ",
        provider_value="  FastAPI Docs ",
        category_value=" Backend ",
        level_value=" Beginner ",
        status_value="in_progress",
        sort_value="newest",
    )
    assert values.scope == "all"
    assert values.search == "fastapi"
    assert values.provider == "fastapi docs"
    assert values.category == "backend"
    assert values.level == "beginner"
    assert values.status == "in_progress"
    assert values.sort == "newest"


def test_build_list_query_params_only_keeps_non_empty_values() -> None:
    params = build_list_query_params(
        search_value="  api  ",
        provider_value="",
        category_value=" Web ",
        level_value=" ",
    )
    assert params == {"q": "api", "category": "Web"}
