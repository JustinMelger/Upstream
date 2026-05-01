"""Pure reducer-style helpers for the Articles page."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.domains.articles.ui_glue import build_facet_select_options, parse_tags


def _filter_articles(
    articles: list[dict[str, Any]] | None,
    *,
    needle: str,
    tag: str,
    author: str,
) -> list[dict[str, Any]]:
    shown = list(articles or [])
    n = needle.strip().lower()
    if n:
        shown = [
            a
            for a in shown
            if n in str(a.get("title") or "").lower()
            or n in str(a.get("url") or "").lower()
            or n in str(a.get("tags") or "").lower()
            or n in str(a.get("created_by") or "").lower()
        ]
    t = tag.strip().lower()
    if t:
        shown = [a for a in shown if t in {x.lower() for x in parse_tags(str(a.get("tags") or ""))}]
    au = author.strip()
    if au:
        shown = [a for a in shown if str(a.get("created_by") or "") == au]
    return shown


def _sort_articles(articles: list[dict[str, Any]] | None, *, sort_key: str) -> list[dict[str, Any]]:
    shown = list(articles or [])
    key = str(sort_key or "").strip()
    if not key:
        return shown
    if key == "newest":

        def _created_key(a: dict[str, Any]) -> tuple[datetime, int]:
            dt = parse_iso_datetime(a.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)
            try:
                aid = int(a.get("id") or 0)
            except (TypeError, ValueError):
                aid = 0
            return (dt, aid)

        return sorted(shown, key=_created_key, reverse=True)
    if key == "title_az":
        return sorted(shown, key=lambda a: str(a.get("title") or "").strip().lower())
    if key == "author_az":
        return sorted(shown, key=lambda a: str(a.get("created_by") or "").strip().lower())
    return shown


def _build_facet_counts(
    articles: list[dict[str, Any]] | None,
    *,
    needle: str,
    tag: str,
    author: str,
) -> tuple[dict[str, int], dict[str, int]]:
    tag_counts: dict[str, int] = {}
    author_counts: dict[str, int] = {}
    shown = _filter_articles(articles, needle=needle, tag=tag, author=author)
    for a in shown:
        for t in parse_tags(str(a.get("tags") or "")):
            tag_counts[t] = int(tag_counts.get(t, 0)) + 1
        au = str(a.get("created_by") or "").strip()
        if au:
            author_counts[au] = int(author_counts.get(au, 0)) + 1
    return tag_counts, author_counts


def compute_facet_state(
    *,
    articles: list[dict[str, Any]],
    needle: str,
    selected_tag: str,
    selected_author: str,
) -> tuple[dict[str, str], dict[str, str], str, str]:
    """Compute facet options and normalized selected values."""
    tag_counts, _ = _build_facet_counts(articles, needle=needle, tag="", author=selected_author)
    _, author_counts = _build_facet_counts(articles, needle=needle, tag=selected_tag, author="")
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
    shown = _filter_articles(articles, needle=needle, tag=tag_value, author=author_value)
    return _sort_articles(shown, sort_key=sort_value)
