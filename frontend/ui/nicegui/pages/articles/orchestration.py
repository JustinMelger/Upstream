"""State orchestration helpers for the Articles page."""

from __future__ import annotations

from typing import Any, Callable

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.pages.articles.actions import ArticlesFacetControls, reset_article_filter_controls
from frontend.ui.nicegui.pages.articles.state import ArticlesPageState
from frontend.ui.nicegui.pages.articles.transitions import (
    begin_articles_load,
    clear_articles_state_on_load_error,
    finalize_articles_load,
)


async def load_articles_page(
    *,
    state: ArticlesPageState,
    controller: Any,
    refresh_btn: Any,
    meta: Any,
    recompute_facets: Callable[[], None],
    refresh_active_filters: Callable[[], None],
    refresh_articles_list_ui: Callable[[], None],
    notify_error: Callable[[str], None],
    compute_meta_text: Callable[[int], str],
) -> None:
    """Load articles list data and refresh dependent UI state."""
    if state.loading:
        return
    ok = False
    load_start = begin_articles_load(page_size=state.page_size)
    state.loading = load_start.loading
    state.visible_count = load_start.visible_count
    refresh_btn.disable()
    meta.text = load_start.meta_text
    refresh_articles_list_ui()
    try:
        bundle = await controller.load_list_bundle()
        state.articles = list(bundle.articles or [])
        state.review_summary_by_article_id = dict(bundle.review_summary_by_article_id or {})
        recompute_facets()
        ok = True
    except ApiError as exc:
        notify_error(str(exc))
        clear_articles_state_on_load_error(state=state)
        recompute_facets()
    finally:
        load_done = finalize_articles_load(ok=ok, article_count=len(state.articles))
        state.loading = load_done.loading
        state.loaded_once = load_done.loaded_once
        meta.text = compute_meta_text(len(state.articles))
        refresh_btn.enable()
        refresh_active_filters()
        refresh_articles_list_ui()


async def perform_create_article(
    *,
    payload: dict[str, Any],
    controller: Any,
    reload_page: Callable[[], Any],
) -> None:
    """Create an article, then refresh page data."""
    await controller.create_article(payload=dict(payload or {}))
    await reload_page()


def refresh_articles_list(
    *,
    state: ArticlesPageState,
    recompute_facets: Callable[[], None],
    refresh_active_filters: Callable[[], None],
    refresh_articles_list_ui: Callable[[], None],
) -> None:
    """Refresh list-level UI after filter updates."""
    state.visible_count = int(state.page_size)
    recompute_facets()
    refresh_active_filters()
    refresh_articles_list_ui()


def clear_articles_filter_values(
    *,
    state: ArticlesPageState,
    controls: ArticlesFacetControls,
    recompute_facets: Callable[[], None],
    refresh_active_filters: Callable[[], None],
    refresh_articles_list_ui: Callable[[], None],
) -> None:
    """Reset all article filters and refresh list-level UI."""
    state.visible_count = int(state.page_size)
    reset_article_filter_controls(controls=controls)
    recompute_facets()
    refresh_active_filters()
    refresh_articles_list_ui()
