"""Articles-related orchestration for the NiceGUI frontend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.datetime_utils import is_recent, parse_iso_datetime


def parse_tags(tags: str | None) -> list[str]:
    """Parse a comma-separated tags string into a normalized list."""
    raw = str(tags or "")
    out: list[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        t = part.strip()
        if not t:
            continue
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def filter_articles(
    articles: list[dict[str, Any]] | None,
    *,
    needle: str,
    tag: str,
    author: str,
) -> list[dict[str, Any]]:
    """Filter articles by search needle, tag, and author."""
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


def sort_articles(articles: list[dict[str, Any]] | None, *, sort_key: str) -> list[dict[str, Any]]:
    """Sort articles based on sort_key."""
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


def build_facet_counts(
    articles: list[dict[str, Any]] | None,
    *,
    needle: str,
    tag: str,
    author: str,
) -> tuple[dict[str, int], dict[str, int]]:
    """Compute tag and author facet counts given the current filters.

    Returns:
        Tuple of `(tag_counts, author_counts)` where each dict maps value -> count.
    """
    tag_counts: dict[str, int] = {}
    author_counts: dict[str, int] = {}
    shown = filter_articles(articles, needle=needle, tag=tag, author=author)
    for a in shown:
        for t in parse_tags(str(a.get("tags") or "")):
            tag_counts[t] = int(tag_counts.get(t, 0)) + 1
        au = str(a.get("created_by") or "").strip()
        if au:
            author_counts[au] = int(author_counts.get(au, 0)) + 1
    return tag_counts, author_counts


def article_is_new(article: dict[str, Any], *, days: int = 7) -> bool:
    """Return True when the article was created recently."""
    return is_recent(parse_iso_datetime(article.get("created_at")), days=days)


async def load_articles(*, api: ApiClient) -> list[dict[str, Any]]:
    """Load all articles for browse/filter UI."""
    return list(await api.get("/articles") or [])
