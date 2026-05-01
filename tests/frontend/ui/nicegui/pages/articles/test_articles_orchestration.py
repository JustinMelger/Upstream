from __future__ import annotations

import pytest

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.domains.articles.actions import ArticlesFacetControls
from frontend.ui.nicegui.domains.articles.orchestration import (
    ArticlesListRefreshDeps,
    clear_articles_filter_values,
    load_articles_page,
    LoadArticlesPageDeps,
    perform_create_article,
    refresh_articles_list,
)
from frontend.ui.nicegui.domains.articles.state import ArticlesPageState


class _Element:
    def __init__(self) -> None:
        self.text = ""
        self.disabled = False

    def disable(self) -> None:
        self.disabled = True

    def enable(self) -> None:
        self.disabled = False


class _Control:
    def __init__(self, value: str = "") -> None:
        self.value = value
        self.updated = 0

    def update(self) -> None:
        self.updated += 1


class _Bundle:
    def __init__(self, *, articles: list[dict], review_summary_by_article_id: dict[int, dict]) -> None:
        self.articles = articles
        self.review_summary_by_article_id = review_summary_by_article_id


class _Controller:
    def __init__(self) -> None:
        self.fail = False
        self.created_payloads: list[dict] = []

    async def load_list_bundle(self) -> _Bundle:
        if self.fail:
            raise ApiError(status_code=503, message="articles_unavailable")
        return _Bundle(
            articles=[{"id": 7, "title": "A"}],
            review_summary_by_article_id={7: {"article_id": 7, "review_count": 2}},
        )

    async def create_article(self, *, payload: dict) -> dict:
        self.created_payloads.append(dict(payload))
        return dict(payload)


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_articles_page_success_populates_state_and_refreshes() -> None:
    state = ArticlesPageState()
    controller = _Controller()
    refresh_btn = _Element()
    meta = _Element()
    events: list[str] = []

    await load_articles_page(
        state=state,
        deps=LoadArticlesPageDeps(
            controller=controller,
            refresh_btn=refresh_btn,
            meta=meta,
            list_refresh=ArticlesListRefreshDeps(
                recompute_facets=lambda: events.append("facets"),
                refresh_active_filters=lambda: events.append("active"),
                refresh_articles_list_ui=lambda: events.append("list"),
            ),
            notify_error=lambda _message: events.append("error"),
            compute_meta_text=lambda count: f"{count} articles",
        ),
    )

    assert state.loaded_once is True
    assert state.loading is False
    assert [int(a.get("id") or 0) for a in state.articles] == [7]
    assert state.review_summary_by_article_id[7]["review_count"] == 2
    assert meta.text == "1 articles"
    assert refresh_btn.disabled is False
    assert "facets" in events and "active" in events and "list" in events
    assert "error" not in events


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_articles_page_failure_clears_state_and_notifies() -> None:
    state = ArticlesPageState(
        articles=[{"id": 1}],
        review_summary_by_article_id={1: {"article_id": 1, "review_count": 1}},
    )
    controller = _Controller()
    controller.fail = True
    refresh_btn = _Element()
    meta = _Element()
    errors: list[str] = []

    await load_articles_page(
        state=state,
        deps=LoadArticlesPageDeps(
            controller=controller,
            refresh_btn=refresh_btn,
            meta=meta,
            list_refresh=ArticlesListRefreshDeps(
                recompute_facets=lambda: None,
                refresh_active_filters=lambda: None,
                refresh_articles_list_ui=lambda: None,
            ),
            notify_error=lambda message: errors.append(message),
            compute_meta_text=lambda count: f"{count} articles",
        ),
    )

    assert state.articles == []
    assert state.review_summary_by_article_id == {}
    assert state.loaded_once is True
    assert refresh_btn.disabled is False
    assert errors == ["503: articles_unavailable"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_articles_page_early_return_when_loading() -> None:
    state = ArticlesPageState(loading=True)
    controller = _Controller()
    refresh_btn = _Element()
    meta = _Element()
    events: list[str] = []

    await load_articles_page(
        state=state,
        deps=LoadArticlesPageDeps(
            controller=controller,
            refresh_btn=refresh_btn,
            meta=meta,
            list_refresh=ArticlesListRefreshDeps(
                recompute_facets=lambda: events.append("facets"),
                refresh_active_filters=lambda: events.append("active"),
                refresh_articles_list_ui=lambda: events.append("list"),
            ),
            notify_error=lambda _message: events.append("error"),
            compute_meta_text=lambda count: f"{count} articles",
        ),
    )

    assert events == []
    assert refresh_btn.disabled is False


@pytest.mark.unit
@pytest.mark.anyio
async def test_perform_create_article_calls_controller_then_reload() -> None:
    controller = _Controller()
    events: list[str] = []

    async def _reload() -> None:
        events.append("reload")

    await perform_create_article(
        payload={"title": "T", "url": "https://example.com"},
        controller=controller,
        reload_page=_reload,
    )

    assert controller.created_payloads == [{"title": "T", "url": "https://example.com"}]
    assert events == ["reload"]


@pytest.mark.unit
def test_refresh_articles_list_resets_visible_and_refreshes() -> None:
    state = ArticlesPageState(page_size=12, visible_count=3)
    events: list[str] = []

    refresh_articles_list(
        state=state,
        deps=ArticlesListRefreshDeps(
            recompute_facets=lambda: events.append("facets"),
            refresh_active_filters=lambda: events.append("active"),
            refresh_articles_list_ui=lambda: events.append("list"),
        ),
    )

    assert state.visible_count == 12
    assert events == ["facets", "active", "list"]


@pytest.mark.unit
def test_clear_articles_filter_values_clears_controls_and_refreshes() -> None:
    state = ArticlesPageState(page_size=10, visible_count=2)
    search = _Control("needle")
    tag = _Control("backend")
    author = _Control("alice")
    sort = _Control("newest")
    calls: list[str] = []

    clear_articles_filter_values(
        state=state,
        controls=ArticlesFacetControls(
            search_input=search,
            tag_filter=tag,
            author_filter=author,
            sort_filter=sort,
        ),
        deps=ArticlesListRefreshDeps(
            recompute_facets=lambda: calls.append("facets"),
            refresh_active_filters=lambda: calls.append("active"),
            refresh_articles_list_ui=lambda: calls.append("list"),
        ),
    )

    assert state.visible_count == 10
    assert search.value == ""
    assert tag.value == ""
    assert author.value == ""
    assert sort.value == ""
    assert calls == ["facets", "active", "list"]
