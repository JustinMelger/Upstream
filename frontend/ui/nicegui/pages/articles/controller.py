"""Controller/orchestration for the Articles page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services.articles_service import load_articles


@dataclass(slots=True)
class ArticlesListBundle:
    """Loaded list payload for the articles page."""

    articles: list[dict[str, Any]]
    review_summary_by_article_id: dict[int, dict[str, Any]]


class ArticlesPageController:
    """Imperative API workflows for `/articles`."""

    def __init__(self, *, api: ApiClient):
        self._api = api

    async def load_list_bundle(self) -> ArticlesListBundle:
        """Load articles and review-summary map."""
        articles = list(await load_articles(api=self._api) or [])
        article_ids = [int(a.get("id") or 0) for a in articles if int(a.get("id") or 0) > 0]
        review_summary_by_article_id: dict[int, dict[str, Any]] = {}
        if article_ids:
            summaries = await self._api.get("/articles/reviews/summary", params={"article_ids": article_ids})
            for row in list(summaries or []):
                if not isinstance(row, dict):
                    continue
                try:
                    aid = int(row.get("article_id") or 0)
                except (TypeError, ValueError):
                    continue
                if aid > 0:
                    review_summary_by_article_id[aid] = row
        return ArticlesListBundle(
            articles=articles,
            review_summary_by_article_id=review_summary_by_article_id,
        )
