from __future__ import annotations

from pydantic import Field, StrictInt, StrictStr

from backend.api.schemas.common import APIModel


class PathReviewPayload(APIModel):
    """Path review payload."""

    id: int
    path_id: int
    rating: int
    text: str
    created_by: str
    created_at: str


class PathReviewCreateRequest(APIModel):
    """Create a path review."""

    rating: StrictInt | None = Field(default=None, ge=1, le=5)
    text: StrictStr | None = None


class PathReviewSummaryItem(APIModel):
    """Review summary for a path."""

    path_id: int
    avg_rating: float
    review_count: int


class DeletePathReviewResponse(APIModel):
    """Path review delete response."""

    deleted: bool
