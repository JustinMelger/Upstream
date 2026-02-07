from __future__ import annotations

from typing import Any

from backend.api.schemas.common import APIModel


class TrackingUpsertRequest(APIModel):
    course_id: Any | None = None
    status: str | None = None


class TrackingDeleteRequest(APIModel):
    course_id: Any | None = None


class TrackingRecordPayload(APIModel):
    colleague_id: str
    course_id: str
    status: str
    updated_at: str


class TrackingDeleteResponse(APIModel):
    removed: int


class TrackingStatsByUserItem(APIModel):
    colleague_id: str
    interested: int
    in_progress: int
    completed: int
