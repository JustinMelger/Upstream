from __future__ import annotations


"""Schemas for AI curation endpoints.

These endpoints return *draft* content only and must not write to the database.
"""

from pydantic import Field, StrictStr

from backend.api.schemas.common import APIModel


class AiPlanRequest(APIModel):
    """AI plan request payload."""

    goal: StrictStr | None = None


class AiDraftCourse(APIModel):
    """Draft course payload (no database id)."""

    title: str
    description: str
    provider: str
    category: str
    level: str
    duration_hours: float | None = None
    url: str = ""


class AiDraftPath(APIModel):
    """Draft path payload (no database id)."""

    name: str
    description: str = ""


class AiPlanResponse(APIModel):
    """AI plan response payload."""

    goal: str
    path: AiDraftPath
    courses: list[AiDraftCourse] = Field(default_factory=list)
