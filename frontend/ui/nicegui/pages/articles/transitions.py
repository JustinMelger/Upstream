"""State transition helpers for the Articles page."""

from __future__ import annotations

from dataclasses import dataclass

from frontend.ui.nicegui.pages.articles.state import ArticlesPageState


@dataclass(frozen=True)
class ArticlesLoadStart:
    loading: bool
    visible_count: int
    meta_text: str


@dataclass(frozen=True)
class ArticlesLoadDone:
    loading: bool
    loaded_once: bool
    meta_text: str


def begin_articles_load(*, page_size: int) -> ArticlesLoadStart:
    """Return state values used when a list load starts."""
    return ArticlesLoadStart(loading=True, visible_count=int(page_size), meta_text="Loading...")


def finalize_articles_load(*, ok: bool, article_count: int) -> ArticlesLoadDone:
    """Return state values used when a list load completes."""
    if ok:
        return ArticlesLoadDone(loading=False, loaded_once=True, meta_text=f"{int(article_count)} articles")
    return ArticlesLoadDone(loading=False, loaded_once=True, meta_text="Failed to load")


def clear_articles_state_on_load_error(*, state: ArticlesPageState) -> None:
    """Clear loaded article data after a failed load."""
    state.articles = []
    state.review_summary_by_article_id = {}
