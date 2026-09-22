from __future__ import annotations

from typing import Any

from pydantic import StrictStr

from backend.api.schemas.common import APIModel


class TrackingUpsertRequest(APIModel):
    """Tracking upsert request payload."""

    course_id: Any | None = None
    status: StrictStr | None = None


class TrackingDeleteRequest(APIModel):
    """Tracking delete request payload."""

    course_id: Any | None = None


class TrackingRecordPayload(APIModel):
    """Tracking record response payload."""

    colleague_id: str
    course_id: str
    status: str
    updated_at: str


class TrackingDeleteResponse(APIModel):
    """Tracking delete response payload."""

    removed: int
