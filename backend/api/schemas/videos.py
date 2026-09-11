from __future__ import annotations

from pydantic import Field, StrictStr

from backend.api.schemas.common import APIModel


class VideoPayload(APIModel):
    """Video response payload."""

    recommendation_note: str | None = Field(default=None, max_length=1000)

    id: int
    title: str
    description: str
    provider: str
    category: str
    url: str
    created_by: str
    created_at: str
    preview_image_url: str = ""


class VideoCreateRequest(APIModel):
    """Video create request payload."""

    recommendation_note: str | None = Field(default=None, max_length=1000)

    title: StrictStr | None = None
    description: StrictStr | None = None
    provider: StrictStr | None = None
    category: StrictStr | None = None
    url: StrictStr | None = None


class VideoUpdateRequest(APIModel):
    """Partial owner/admin edit; omitted fields are preserved."""

    title: str | None = None
    url: str | None = None
    recommendation_note: str | None = Field(default=None, max_length=1000)
    description: str | None = None
    provider: str | None = None
    category: str | None = None
