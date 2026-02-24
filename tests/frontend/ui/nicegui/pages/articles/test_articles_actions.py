from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.articles.actions import (
    ArticlesFacetControls,
    build_article_card_actions,
    build_articles_facet_controls,
    clear_article_filter_and_refresh,
    clear_article_filter_by_key,
    recompute_article_facet_controls,
    recompute_article_facet_controls_for_search,
    reset_article_filter_controls,
)


@pytest.mark.unit
@pytest.mark.anyio
async def test_build_article_card_actions_wires_view_and_review_callbacks() -> None:
    calls: list[str] = []

    async def _open_details(article: dict, focus_reviews: bool) -> None:
        calls.append(f"{int(article.get('id') or 0)}:{focus_reviews}")

    actions = build_article_card_actions(
        article_row={"id": 5, "title": "X"},
        on_open_details=_open_details,
    )
    await actions.on_view()
    await actions.on_review()

    assert calls == ["5:False", "5:True"]


class _Control:
    def __init__(self, value="") -> None:
        self.value = value
        self.options = {}
        self.updated = 0

    def update(self) -> None:
        self.updated += 1


@pytest.mark.unit
def test_build_articles_facet_controls_returns_typed_bundle() -> None:
    search = _Control("q")
    tag = _Control("t")
    author = _Control("a")
    sort = _Control("s")
    controls = build_articles_facet_controls(
        search_input=search,
        tag_filter=tag,
        author_filter=author,
        sort_filter=sort,
    )
    assert isinstance(controls, ArticlesFacetControls)
    assert controls.search_input is search
    assert controls.tag_filter is tag
    assert controls.author_filter is author
    assert controls.sort_filter is sort


@pytest.mark.unit
def test_recompute_article_facet_controls_updates_options_and_values() -> None:
    controls = ArticlesFacetControls(
        search_input=_Control(""),
        tag_filter=_Control(""),
        author_filter=_Control(""),
        sort_filter=_Control(""),
    )
    articles = [
        {"id": 1, "created_by": "alice", "tags": "fastapi,backend"},
        {"id": 2, "created_by": "bob", "tags": "python"},
    ]

    recompute_article_facet_controls(controls=controls, articles=articles)

    assert controls.tag_filter.options
    assert controls.author_filter.options
    assert controls.tag_filter.updated == 1
    assert controls.author_filter.updated == 1


@pytest.mark.unit
def test_recompute_article_facet_controls_for_search_uses_explicit_search_value() -> None:
    controls = ArticlesFacetControls(
        search_input=_Control("ignored"),
        tag_filter=_Control(""),
        author_filter=_Control(""),
        sort_filter=_Control(""),
    )
    articles = [
        {"id": 1, "created_by": "alice", "tags": "fastapi,backend"},
        {"id": 2, "created_by": "bob", "tags": "python"},
    ]

    recompute_article_facet_controls_for_search(
        controls=controls,
        articles=articles,
        search_value="python",
    )

    assert "python" in controls.tag_filter.options
    assert "fastapi" not in controls.tag_filter.options


@pytest.mark.unit
def test_clear_article_filter_by_key_clears_expected_control() -> None:
    controls = ArticlesFacetControls(
        search_input=_Control("needle"),
        tag_filter=_Control("backend"),
        author_filter=_Control("alice"),
        sort_filter=_Control("newest"),
    )

    assert clear_article_filter_by_key(key="search", controls=controls) is True
    assert controls.search_input.value == ""
    assert controls.search_input.updated == 1

    assert clear_article_filter_by_key(key="tag", controls=controls) is True
    assert controls.tag_filter.value == ""
    assert controls.tag_filter.updated == 1

    assert clear_article_filter_by_key(key="author", controls=controls) is True
    assert controls.author_filter.value == ""
    assert controls.author_filter.updated == 1

    assert clear_article_filter_by_key(key="sort", controls=controls) is True
    assert controls.sort_filter.value == ""
    assert controls.sort_filter.updated == 1

    assert clear_article_filter_by_key(key="unknown", controls=controls) is False


@pytest.mark.unit
def test_reset_article_filter_controls_clears_all_values() -> None:
    controls = ArticlesFacetControls(
        search_input=_Control("needle"),
        tag_filter=_Control("backend"),
        author_filter=_Control("alice"),
        sort_filter=_Control("newest"),
    )

    reset_article_filter_controls(controls=controls)

    assert controls.search_input.value == ""
    assert controls.tag_filter.value == ""
    assert controls.author_filter.value == ""
    assert controls.sort_filter.value == ""
    assert controls.search_input.updated == 1
    assert controls.tag_filter.updated == 1
    assert controls.author_filter.updated == 1
    assert controls.sort_filter.updated == 1


@pytest.mark.unit
def test_clear_article_filter_and_refresh_runs_refresh_when_key_handled() -> None:
    controls = ArticlesFacetControls(
        search_input=_Control("needle"),
        tag_filter=_Control("backend"),
        author_filter=_Control("alice"),
        sort_filter=_Control("newest"),
    )
    events: list[str] = []

    clear_article_filter_and_refresh(
        key="search",
        controls=controls,
        refresh_list=lambda: events.append("refresh"),
    )
    clear_article_filter_and_refresh(
        key="unknown",
        controls=controls,
        refresh_list=lambda: events.append("refresh"),
    )

    assert controls.search_input.value == ""
    assert events == ["refresh"]
