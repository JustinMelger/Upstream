"""Pure reducer-style helpers for the Articles page."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.pages.articles.ui_glue import build_facet_select_options
from frontend.ui.nicegui.services.articles_service import build_facet_counts, filter_articles, sort_articles


def compute_facet_state(
    *,
    articles: list[dict[str, Any]],
    needle: str,
    selected_tag: str,
    selected_author: str,
) -> tuple[dict[str, str], dict[str, str], str, str]:
    """Compute facet options and normalized selected values."""
    tag_counts, _ = build_facet_counts(articles, needle=needle, tag="", author=selected_author)
    _, author_counts = build_facet_counts(articles, needle=needle, tag=selected_tag, author="")
    tag_options, author_options = build_facet_select_options(
        tag_counts=tag_counts,
        author_counts=author_counts,
    )
    next_tag = selected_tag if (selected_tag and selected_tag in tag_options) else ""
    next_author = selected_author if (selected_author and selected_author in author_options) else ""
    return tag_options, author_options, next_tag, next_author


def derive_shown_articles(
    *,
    articles: list[dict[str, Any]],
    needle: str,
    tag_value: str,
    author_value: str,
    sort_value: str,
) -> list[dict[str, Any]]:
    """Apply list filters and sort order for rendering."""
    shown = filter_articles(articles, needle=needle, tag=tag_value, author=author_value)
    return sort_articles(shown, sort_key=sort_value)
