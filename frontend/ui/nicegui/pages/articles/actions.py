"""Card-level actions for the Articles page."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ArticleCardActions:
    """Callback bundle for a single article card."""

    on_view: Callable[[], Awaitable[None]]
    on_review: Callable[[], Awaitable[None]]


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
