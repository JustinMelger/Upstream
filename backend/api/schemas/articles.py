from __future__ import annotations

from typing import Optional

from backend.api.schemas.common import APIModel


class ArticlePayload(APIModel):
    """Article payload returned by the API."""

    id: int
    title: str
    url: str
    tags: Optional[str] = None
    created_by: str
    created_at: str


class ArticleCreateRequest(APIModel):
    """Request body for creating an article."""

    title: str
    url: str
    tags: Optional[str] = None
