"""View-model mapping helpers for article cards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.datetime_utils import format_date
from frontend.ui.nicegui.core.summary_formatters import format_review_summary
from frontend.ui.nicegui.domains.articles.ui_glue import article_is_new, parse_tags
from frontend.ui.nicegui.domains.courses.media import preferred_preview_image_url


@dataclass(slots=True)
class ArticleCardView:
    """Display-ready values for rendering an article card."""

    is_new: bool
    tags: list[str]
    summary_text: str
    subtitle_text: str
    thumbnail_url: str


def map_article_card_view(
    *,
    article_row: dict[str, Any],
    review_summary_row: dict[str, Any] | None,
) -> ArticleCardView:
    """Map raw article + summary rows into display-ready card values."""
    created_by = str(article_row.get("created_by") or "").strip()
    created_at = str(article_row.get("created_at") or "").strip()
    summary = format_review_summary(review_summary_row, style="star")
    subtitle_bits = [
        f"Shared by {created_by}" if created_by else "",
        format_date(created_at),
    ]
    return ArticleCardView(
        is_new=bool(article_is_new(article_row)),
        tags=parse_tags(str(article_row.get("tags") or "")),
        summary_text=summary,
        subtitle_text=" · ".join([bit for bit in subtitle_bits if bit]),
        thumbnail_url=preferred_preview_image_url(article_row.get("preview_image_url")),
    )
