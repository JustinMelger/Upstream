from __future__ import annotations

from frontend.ui.nicegui.pages.articles.reducers import compute_facet_state, derive_shown_articles


def test_compute_facet_state_returns_options_and_normalized_selection() -> None:
    articles = [
        {"title": "A", "tags": "api", "created_by": "alice"},
        {"title": "B", "tags": "backend", "created_by": "bob"},
    ]
    tag_options, author_options, next_tag, next_author = compute_facet_state(
        articles=articles,
        needle="",
        selected_tag="api",
        selected_author="alice",
    )
    assert tag_options[""] == "Any tag"
    assert author_options[""] == "Anyone"
    assert next_tag == "api"
    assert next_author == "alice"


def test_compute_facet_state_empty_data_clears_selected_values() -> None:
    tag_options, author_options, next_tag, next_author = compute_facet_state(
        articles=[],
        needle="anything",
        selected_tag="api",
        selected_author="alice",
    )
    assert tag_options == {"": "Any tag"}
    assert author_options == {"": "Anyone"}
    assert next_tag == ""
    assert next_author == ""


def test_derive_shown_articles_applies_filter_and_sort() -> None:
    articles = [
        {"title": "Z item", "tags": "api", "created_by": "alice"},
        {"title": "A item", "tags": "api", "created_by": "alice"},
        {"title": "B item", "tags": "web", "created_by": "bob"},
    ]
    shown = derive_shown_articles(
        articles=articles,
        needle="item",
        tag_value="api",
        author_value="alice",
        sort_value="title_az",
    )
    assert [str(a.get("title")) for a in shown] == ["A item", "Z item"]
