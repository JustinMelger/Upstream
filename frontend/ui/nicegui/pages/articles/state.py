"""State model for the Articles page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ArticlesPageState:
    """Mutable UI state for `/articles`."""

    articles: list[dict[str, Any]] = field(default_factory=list)
    review_summary_by_article_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    loading: bool = False
    loaded_once: bool = False
    page_size: int = 10
    visible_count: int = 10
