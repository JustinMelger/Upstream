from __future__ import annotations

from pydantic import Field, StrictInt, StrictStr

from backend.api.schemas.common import APIModel


class CourseReviewPayload(APIModel):
    """Course review payload."""

    id: int
    course_id: int
    rating: int
    text: str
    created_by: str
    created_at: str


class CourseReviewCreateRequest(APIModel):
    """Create a course review."""

    rating: StrictInt | None = Field(default=None, ge=1, le=5)
    text: StrictStr | None = None


class DeleteCourseReviewResponse(APIModel):
    """Course review delete response."""

    deleted: bool
