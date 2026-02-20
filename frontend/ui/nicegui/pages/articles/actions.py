"""Card-level actions for the Articles page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.pages.articles.filters import normalize_articles_filter_values
from frontend.ui.nicegui.pages.articles.reducers import compute_facet_state


@dataclass(slots=True)
class ArticleCardActions:
    """Callback bundle for a single article card."""

    on_view: Callable[[], Awaitable[None]]
    on_review: Callable[[], Awaitable[None]]


@dataclass(slots=True)
class ArticlesFacetControls:
    """Filter control handles used for facet recomputation/reset."""

    search_input: Any
    tag_filter: Any
    author_filter: Any
    sort_filter: Any


def build_articles_facet_controls(
    *,
    search_input: Any,
    tag_filter: Any,
    author_filter: Any,
    sort_filter: Any,
) -> ArticlesFacetControls:
    """Create a typed facet-control bundle."""
    return ArticlesFacetControls(
        search_input=search_input,
        tag_filter=tag_filter,
        author_filter=author_filter,
        sort_filter=sort_filter,
    )


def build_article_card_actions(
    *,
    article_row: dict[str, Any],
    on_open_details: Callable[[dict[str, Any], bool], Awaitable[None]],
) -> ArticleCardActions:
    """Build per-card callbacks for view/review actions."""

    async def _view() -> None:
        await on_open_details(article_row, False)

    async def _review() -> None:
        await on_open_details(article_row, True)

    return ArticleCardActions(on_view=_view, on_review=_review)


def recompute_article_facet_controls(
    *,
    controls: ArticlesFacetControls,
    articles: list[dict[str, Any]],
) -> None:
    """Recompute facet options/values based on current controls + visible data."""
    recompute_article_facet_controls_for_search(
        controls=controls,
        articles=articles,
        search_value=str(controls.search_input.value or ""),
    )


def recompute_article_facet_controls_for_search(
    *,
    controls: ArticlesFacetControls,
    articles: list[dict[str, Any]],
    search_value: str,
) -> None:
    """Recompute facet options/values using an explicit search value."""
    tag_filter = controls.tag_filter
    author_filter = controls.author_filter
    if tag_filter is None or author_filter is None:
        return

    normalized = normalize_articles_filter_values(
        search_value=str(search_value or ""),
        tag_value=str(tag_filter.value or ""),
        author_value=str(author_filter.value or ""),
        sort_value=str(controls.sort_filter.value or "") if controls.sort_filter is not None else "",
    )
    tag_options, author_options, next_tag, next_author = compute_facet_state(
        articles=articles,
        needle=normalized.search,
        selected_tag=normalized.tag,
        selected_author=normalized.author,
    )
    tag_filter.options = tag_options
    author_filter.options = author_options
    tag_filter.value = next_tag
    author_filter.value = next_author
    tag_filter.update()
    author_filter.update()


def clear_article_filter_by_key(*, key: str, controls: ArticlesFacetControls) -> bool:
    """Clear one filter control by key; return whether a key was handled."""
    key_value = str(key or "").strip()
    if key_value == "search":
        controls.search_input.value = ""
        controls.search_input.update()
        return True
    if key_value == "tag" and controls.tag_filter is not None:
        controls.tag_filter.value = ""
        controls.tag_filter.update()
        return True
    if key_value == "author" and controls.author_filter is not None:
        controls.author_filter.value = ""
        controls.author_filter.update()
        return True
    if key_value == "sort" and controls.sort_filter is not None:
        controls.sort_filter.value = ""
        controls.sort_filter.update()
        return True
    return False


def reset_article_filter_controls(*, controls: ArticlesFacetControls) -> None:
    """Clear all filter controls and update widgets."""
    controls.search_input.value = ""
    controls.search_input.update()
    if controls.tag_filter is not None:
        controls.tag_filter.value = ""
        controls.tag_filter.update()
    if controls.author_filter is not None:
        controls.author_filter.value = ""
        controls.author_filter.update()
    if controls.sort_filter is not None:
        controls.sort_filter.value = ""
        controls.sort_filter.update()


def clear_article_filter_and_refresh(
    *,
    key: str,
    controls: ArticlesFacetControls,
    refresh_list: Callable[[], None],
) -> None:
    """Clear one filter by key and refresh list-level UI when handled."""
    if clear_article_filter_by_key(key=key, controls=controls):
        refresh_list()
