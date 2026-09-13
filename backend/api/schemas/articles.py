from __future__ import annotations

from typing import Optional

from pydantic import Field

from backend.api.schemas.common import APIModel


class ArticlePayload(APIModel):
    """Article payload returned by the API."""

    description: str | None = Field(default=None, max_length=2000)

    recommendation_note: str | None = Field(default=None, max_length=1000)

    id: int
    title: str
    url: str
    preview_image_url: str = ""
    tags: Optional[str] = None
    created_by: str
    created_at: str


class ArticleCreateRequest(APIModel):
    """Request body for creating an article."""

    description: str | None = Field(default=None, max_length=2000)

    recommendation_note: str | None = Field(default=None, max_length=1000)

    title: str
    url: str
    tags: Optional[str] = None


class ArticleUpdateRequest(APIModel):
    """Partial owner/admin edit; omitted fields are preserved."""

    title: str | None = None
    url: str | None = None
    description: str | None = Field(default=None, max_length=2000)

    recommendation_note: str | None = Field(default=None, max_length=1000)
    tags: str | None = None
