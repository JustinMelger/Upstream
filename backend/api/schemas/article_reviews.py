from __future__ import annotations

from pydantic import Field, StrictInt, StrictStr

from backend.api.schemas.common import APIModel


class ArticleReviewPayload(APIModel):
    """Article review payload."""

    id: int
    article_id: int
    rating: int
    text: str
    created_by: str
    created_at: str


class ArticleReviewCreateRequest(APIModel):
    """Create an article review."""

    rating: StrictInt | None = Field(default=None, ge=1, le=5)
    text: StrictStr | None = None


class ArticleReviewSummaryItem(APIModel):
    """Review summary for an article."""

    article_id: int
    avg_rating: float
    review_count: int


class DeleteArticleReviewResponse(APIModel):
    """Article review delete response."""

    deleted: bool
