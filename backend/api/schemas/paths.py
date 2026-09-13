from __future__ import annotations

from pydantic import Field, StrictInt, StrictStr

from backend.api.schemas.common import APIModel


class PathListItem(APIModel):
    """Path list item payload."""

    recommendation_note: str | None = Field(default=None, max_length=1000)

    id: int
    name: str
    description: str
    created_by: str | None
    course_count: int = 0


class PathDetailResponse(APIModel):
    """Path detail response payload."""

    recommendation_note: str | None = Field(default=None, max_length=1000)

    id: int
    name: str
    description: str
    created_by: str | None
    items: list["PathLearningItem"] = Field(default_factory=list)


class PathLearningItem(APIModel):
    """Typed learning-item payload embedded within a path."""

    type: str
    id: int
    title: str
    description: str = ""
    provider: str = ""
    category: str = ""
    level: str = ""
    duration_hours: float | None = None
    url: str = ""
    preview_image_url: str = ""


class PathItemRequest(APIModel):
    """Typed learning-item reference used in path mutation payloads."""

    type: StrictStr | None = None
    id: StrictInt | None = None
    position: StrictInt | None = None


class PathCreateRequest(APIModel):
    """Path create request payload."""

    recommendation_note: str | None = Field(default=None, max_length=1000)

    name: StrictStr | None = None
    description: StrictStr | None = None
    items: list[PathItemRequest] = Field(default_factory=list)


class PathUpdateRequest(APIModel):
    """Path update request payload."""

    recommendation_note: str | None = Field(default=None, max_length=1000)

    name: StrictStr | None = None
    description: StrictStr | None = None
    items: list[PathItemRequest] = Field(default_factory=list)


class DeletePathResponse(APIModel):
    """Path delete response payload."""

    deleted: bool


class SelectPathResponse(APIModel):
    """Path select response payload."""

    colleague_id: str
    path_id: str
    created_at: str


class UnselectPathResponse(APIModel):
    """Path unselect response payload."""

    removed: int


class PathStatusRequest(APIModel):
    """Path status update request payload."""

    status: StrictStr | None = None


class PathStatusResponse(APIModel):
    """Path status update response payload."""

    updated: int


class SelectedPathItem(APIModel):
    """Selected path item payload."""

    id: int
    name: str
    description: str
    status: str
