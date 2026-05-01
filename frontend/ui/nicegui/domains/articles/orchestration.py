"""State orchestration helpers for the Articles page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.domains.articles.actions import ArticlesFacetControls, reset_article_filter_controls
from frontend.ui.nicegui.domains.articles.state import ArticlesPageState
from frontend.ui.nicegui.domains.articles.transitions import (
    begin_articles_load,
    clear_articles_state_on_load_error,
    finalize_articles_load,
)


@dataclass(frozen=True, slots=True)
class ArticlesListRefreshDeps:
    """Dependencies required to refresh list-level Articles UI blocks."""

    recompute_facets: Callable[[], None]
    refresh_active_filters: Callable[[], None]
    refresh_articles_list_ui: Callable[[], None]


@dataclass(frozen=True, slots=True)
class LoadArticlesPageDeps:
    """Dependencies required to load and refresh the Articles page."""

    controller: Any
    refresh_btn: Any
    meta: Any
    list_refresh: ArticlesListRefreshDeps
    notify_error: Callable[[str], None]
    compute_meta_text: Callable[[int], str]


async def load_articles_page(
    *,
    state: ArticlesPageState,
    deps: LoadArticlesPageDeps,
) -> None:
    """Load articles list data and refresh dependent UI state."""
    if state.loading:
        return
    ok = False
    load_start = begin_articles_load(page_size=state.page_size)
    state.loading = load_start.loading
    state.visible_count = load_start.visible_count
    deps.refresh_btn.disable()
    deps.meta.text = load_start.meta_text
    deps.list_refresh.refresh_articles_list_ui()
    try:
        bundle = await deps.controller.load_list_bundle()
        state.articles = list(bundle.articles or [])
        state.review_summary_by_article_id = dict(bundle.review_summary_by_article_id or {})
        deps.list_refresh.recompute_facets()
        ok = True
    except ApiError as exc:
        deps.notify_error(str(exc))
        clear_articles_state_on_load_error(state=state)
        deps.list_refresh.recompute_facets()
    finally:
        load_done = finalize_articles_load(ok=ok, article_count=len(state.articles))
        state.loading = load_done.loading
        state.loaded_once = load_done.loaded_once
        deps.meta.text = deps.compute_meta_text(len(state.articles))
        deps.refresh_btn.enable()
        deps.list_refresh.refresh_active_filters()
        deps.list_refresh.refresh_articles_list_ui()


async def perform_create_article(
    *,
    payload: dict[str, Any],
    controller: Any,
    reload_page: Callable[[], Any],
) -> dict[str, Any]:
    """Create an article, then refresh page data."""
    created = dict(await controller.create_article(payload=dict(payload or {})) or {})
    await reload_page()
    return created


def refresh_articles_list(
    *,
    state: ArticlesPageState,
    deps: ArticlesListRefreshDeps,
) -> None:
    """Refresh list-level UI after filter updates."""
    state.visible_count = int(state.page_size)
    deps.recompute_facets()
    deps.refresh_active_filters()
    deps.refresh_articles_list_ui()


def clear_articles_filter_values(
    *,
    state: ArticlesPageState,
    controls: ArticlesFacetControls,
    deps: ArticlesListRefreshDeps,
) -> None:
    """Reset all article filters and refresh list-level UI."""
    state.visible_count = int(state.page_size)
    reset_article_filter_controls(controls=controls)
    deps.recompute_facets()
    deps.refresh_active_filters()
    deps.refresh_articles_list_ui()
