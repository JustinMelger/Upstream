"""Pure UI glue helpers for the Articles page."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from frontend.ui.nicegui.core.datetime_utils import is_recent, parse_iso_datetime


@dataclass(frozen=True)
class ActiveFilterChip:
    """Descriptor for a removable active-filter chip."""

    key: str
    label: str


def build_facet_select_options(
    *,
    tag_counts: dict[str, int],
    author_counts: dict[str, int],
) -> tuple[dict[str, str], dict[str, str]]:
    """Build sorted tag/author select options with counts."""
    tag_options = {"": "Any tag"} | {t: f"{t} ({tag_counts[t]})" for t in sorted(tag_counts.keys(), key=lambda x: x.lower())}
    author_options = {"": "Anyone"} | {
        a: f"{a} ({author_counts[a]})" for a in sorted(author_counts.keys(), key=lambda x: x.lower())
    }
    return tag_options, author_options


def build_active_filter_chips(
    *,
    search_value: str,
    tag_value: str,
    author_value: str,
    sort_value: str,
    sort_options: dict[str, str],
) -> list[ActiveFilterChip]:
    """Build active filter chips for current article filter state."""
    chips: list[ActiveFilterChip] = []
    search = str(search_value or "").strip()
    if search:
        chips.append(ActiveFilterChip(key="search", label=f"Search: {search}"))

    tag = str(tag_value or "").strip()
    if tag:
        chips.append(ActiveFilterChip(key="tag", label=f"Tag: {tag}"))

    author = str(author_value or "").strip()
    if author:
        chips.append(ActiveFilterChip(key="author", label=f"Shared by: {author}"))

    sort_key = str(sort_value or "").strip()
    if sort_key:
        chips.append(ActiveFilterChip(key="sort", label=f"Sort: {str(sort_options.get(sort_key) or sort_key)}"))
    return chips


def compute_articles_meta_text(*, article_count: int) -> str:
    """Build the top-bar list meta text."""
    return f"{int(article_count)} articles"


def compute_expanded_visible_count(*, current_visible: int, total_count: int, page_size: int) -> int:
    """Return next visible count for load-more pagination."""
    return min(int(total_count), int(current_visible) + int(page_size))


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


def article_is_new(article: dict[str, Any], *, days: int = 7) -> bool:
    """Return True when the article was created recently."""
    created_at: datetime | None = parse_iso_datetime(article.get("created_at")) if isinstance(article, dict) else None
    return is_recent(created_at, days=days)
