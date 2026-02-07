from __future__ import annotations

from pydantic import Field, StrictInt, StrictStr

from backend.api.schemas.common import APIModel


class PathListItem(APIModel):
    id: int
    name: str
    description: str


class PathCourseItem(APIModel):
    id: int
    title: str
    provider: str
    category: str
    level: str
    duration_hours: float | None
    url: str


class PathDetailResponse(APIModel):
    id: int
    name: str
    description: str
    courses: list[PathCourseItem]


class PathCreateRequest(APIModel):
    name: StrictStr | None = None
    description: StrictStr | None = None
    course_ids: list[StrictInt] = Field(default_factory=list)


class PathUpdateRequest(APIModel):
    name: StrictStr | None = None
    description: StrictStr | None = None
    course_ids: list[StrictInt] = Field(default_factory=list)


class DeletePathResponse(APIModel):
    deleted: bool


class SelectPathResponse(APIModel):
    colleague_id: str
    path_id: str
    created_at: str


class UnselectPathResponse(APIModel):
    removed: int


class PathStatusRequest(APIModel):
    status: StrictStr | None = None


class PathStatusResponse(APIModel):
    updated: int


class SelectedPathItem(APIModel):
    id: int
    name: str
    description: str
    status: str
