from __future__ import annotations

from typing import Any

from pydantic import StrictStr

from backend.api.schemas.common import APIModel


class CoursePayload(APIModel):
    id: int
    title: str
    provider: str
    category: str
    level: str
    duration_hours: float | None
    url: str
    created_at: str | None


class CourseCreateRequest(APIModel):
    title: StrictStr | None = None
    provider: StrictStr | None = None
    category: StrictStr | None = None
    level: StrictStr | None = None
    duration_hours: Any | None = None
    url: StrictStr | None = None


class CourseUpdateRequest(APIModel):
    title: StrictStr | None = None
    provider: StrictStr | None = None
    category: StrictStr | None = None
    level: StrictStr | None = None
    duration_hours: Any | None = None
    url: StrictStr | None = None


class DeleteCourseResponse(APIModel):
    deleted: bool
