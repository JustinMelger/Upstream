from __future__ import annotations

from frontend.ui.nicegui.pages.articles.filters import build_articles_list_query_params, normalize_articles_filter_values


def test_normalize_articles_filter_values_normalizes_fields() -> None:
    values = normalize_articles_filter_values(
        search_value="  FastAPI ",
        tag_value=" backend ",
        author_value=" alice ",
        sort_value=" newest ",
    )
    assert values.search == "FastAPI"
    assert values.tag == "backend"
    assert values.author == "alice"
    assert values.sort == "newest"


def test_build_articles_list_query_params_only_includes_non_empty_search() -> None:
    assert build_articles_list_query_params(search_value="  api ") == {"q": "api"}
    assert build_articles_list_query_params(search_value=" ") == {}
