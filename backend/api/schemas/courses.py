from __future__ import annotations

from typing import Any

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
    title: str | None = None
    provider: str | None = None
    category: str | None = None
    level: str | None = None
    duration_hours: Any | None = None
    url: str | None = None


class CourseUpdateRequest(APIModel):
    title: str | None = None
    provider: str | None = None
    category: str | None = None
    level: str | None = None
    duration_hours: Any | None = None
    url: str | None = None


class DeleteCourseResponse(APIModel):
    deleted: bool
