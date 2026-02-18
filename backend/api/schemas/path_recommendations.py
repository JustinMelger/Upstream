from __future__ import annotations

from pydantic import StrictStr

from backend.api.schemas.common import APIModel


class PathRecommendationPayload(APIModel):
    """Path recommendation payload."""

    id: int
    path_id: int
    note: str
    created_by: str
    created_at: str


class PathRecommendationCreateRequest(APIModel):
    """Create/update path recommendation request."""

    note: StrictStr | None = None


class PathRecommendationSummaryItem(APIModel):
    """Recommendation summary for a path."""

    path_id: int
    recommendation_count: int


class DeletePathRecommendationResponse(APIModel):
    """Path recommendation delete response."""

    deleted: bool
