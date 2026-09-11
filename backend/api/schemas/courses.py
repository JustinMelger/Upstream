from __future__ import annotations

from typing import Any

from pydantic import Field, StrictStr

from backend.api.schemas.common import APIModel


class CoursePayload(APIModel):
    """Course response payload."""

    recommendation_note: str | None = Field(default=None, max_length=1000)

    id: int
    title: str
    description: str
    learning_outcomes: str
    prerequisites: str
    language: str
    provider: str
    category: str
    level: str
    duration_hours: float | None
    url: str
    created_at: str | None
    created_by: str | None
    search_document: str


class CourseCreateRequest(APIModel):
    """Course create request payload."""

    recommendation_note: str | None = Field(default=None, max_length=1000)

    title: StrictStr | None = None
    description: StrictStr | None = None
    learning_outcomes: StrictStr | None = None
    prerequisites: StrictStr | None = None
    language: StrictStr | None = None
    provider: StrictStr | None = None
    category: StrictStr | None = None
    level: StrictStr | None = None
    duration_hours: Any | None = None
    url: StrictStr | None = None


class CourseUpdateRequest(APIModel):
    """Course update request payload."""

    recommendation_note: str | None = Field(default=None, max_length=1000)

    title: StrictStr | None = None
    description: StrictStr | None = None
    learning_outcomes: StrictStr | None = None
    prerequisites: StrictStr | None = None
    language: StrictStr | None = None
    provider: StrictStr | None = None
    category: StrictStr | None = None
    level: StrictStr | None = None
    duration_hours: Any | None = None
    url: StrictStr | None = None


class DeleteCourseResponse(APIModel):
    """Course delete response payload."""

    deleted: bool
