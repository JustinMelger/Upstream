"""Details dialog flow orchestration for the Articles page."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.datetime_utils import format_date
from frontend.ui.nicegui.core.summary_formatters import format_review_summary
from frontend.ui.nicegui.pages.articles.dialogs import open_article_details_dialog
from frontend.ui.nicegui.pages.articles.state import ArticlesPageState


async def open_article_details_flow(
    *,
    article: dict[str, Any],
    focus_reviews: bool,
    username: str,
    is_admin: bool,
    controller: Any,
    state: ArticlesPageState,
) -> None:
    """Open article details dialog using page controller/state callbacks."""
    await open_article_details_dialog(
        article=article,
        focus_reviews=focus_reviews,
        username=username,
        is_admin=is_admin,
        load_reviews=lambda _article_id: controller.load_article_reviews(article_id=int(_article_id)),
        save_review=lambda _article_id, _rating, _text: controller.save_article_review(
            article_id=int(_article_id),
            rating=int(_rating),
            text=str(_text or ""),
        ),
        delete_review=lambda _article_id, _review_id: controller.delete_article_review(
            article_id=int(_article_id),
            review_id=int(_review_id),
        ),
        review_summary_by_article_id=state.review_summary_by_article_id,
        format_review_summary=lambda row: format_review_summary(row, style="fraction"),
        format_date=format_date,
    )
