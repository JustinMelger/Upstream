from __future__ import annotations

from pydantic import Field, StrictInt, StrictStr

from backend.api.schemas.common import APIModel


class VideoReviewPayload(APIModel):
    """Video review payload."""

    id: int
    video_id: int
    rating: int
    text: str
    created_by: str
    created_at: str


class VideoReviewCreateRequest(APIModel):
    """Create a video review."""

    rating: StrictInt | None = Field(default=None, ge=1, le=5)
    text: StrictStr | None = None


class VideoReviewSummaryItem(APIModel):
    """Review summary for a video."""

    video_id: int
    avg_rating: float
    review_count: int


class DeleteVideoReviewResponse(APIModel):
    """Video review delete response."""

    deleted: bool
