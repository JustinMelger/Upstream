from __future__ import annotations

from pydantic import StrictStr

from backend.api.schemas.common import APIModel


class CourseRecommendationPayload(APIModel):
    """Course recommendation payload."""

    id: int
    course_id: int
    note: str
    created_by: str
    created_at: str


class CourseRecommendationCreateRequest(APIModel):
    """Create/update course recommendation request."""

    note: StrictStr | None = None


class CourseRecommendationSummaryItem(APIModel):
    """Recommendation summary for a course."""

    course_id: int
    recommendation_count: int


class DeleteCourseRecommendationResponse(APIModel):
    """Course recommendation delete response."""

    deleted: bool
