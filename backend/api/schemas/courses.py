from __future__ import annotations

from typing import Any

from pydantic import StrictStr

from backend.api.schemas.common import APIModel


class CoursePayload(APIModel):
    """Course response payload."""

    id: int
    title: str
    description: str
    provider: str
    category: str
    level: str
    duration_hours: float | None
    url: str
    created_at: str | None
    created_by: str | None


class CourseCreateRequest(APIModel):
    """Course create request payload."""

    title: StrictStr | None = None
    description: StrictStr | None = None
    provider: StrictStr | None = None
    category: StrictStr | None = None
    level: StrictStr | None = None
    duration_hours: Any | None = None
    url: StrictStr | None = None


class CourseUpdateRequest(APIModel):
    """Course update request payload."""

    title: StrictStr | None = None
    description: StrictStr | None = None
    provider: StrictStr | None = None
    category: StrictStr | None = None
    level: StrictStr | None = None
    duration_hours: Any | None = None
    url: StrictStr | None = None


class DeleteCourseResponse(APIModel):
    """Course delete response payload."""

    deleted: bool
