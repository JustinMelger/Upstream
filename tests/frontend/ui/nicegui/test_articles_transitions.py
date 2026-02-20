from __future__ import annotations

from frontend.ui.nicegui.pages.articles.state import ArticlesPageState
from frontend.ui.nicegui.pages.articles.transitions import (
    begin_articles_load,
    clear_articles_state_on_load_error,
    finalize_articles_load,
)


def test_begin_articles_load_sets_loading_defaults() -> None:
    out = begin_articles_load(page_size=10)
    assert out.loading is True
    assert out.visible_count == 10
    assert out.meta_text == "Loading..."


def test_finalize_articles_load_success() -> None:
    out = finalize_articles_load(ok=True, article_count=7)
    assert out.loading is False
    assert out.loaded_once is True
    assert out.meta_text == "7 articles"


def test_finalize_articles_load_failure() -> None:
    out = finalize_articles_load(ok=False, article_count=0)
    assert out.loading is False
    assert out.loaded_once is True
    assert out.meta_text == "Failed to load"


def test_clear_articles_state_on_load_error() -> None:
    state = ArticlesPageState(
        articles=[{"id": 1, "title": "x"}],
        review_summary_by_article_id={1: {"review_count": 2}},
    )
    clear_articles_state_on_load_error(state=state)
    assert state.articles == []
    assert state.review_summary_by_article_id == {}
