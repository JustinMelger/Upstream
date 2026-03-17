from __future__ import annotations

from pydantic import StrictStr

from backend.api.schemas.common import APIModel


class VideoPayload(APIModel):
    """Video response payload."""

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

    title: StrictStr | None = None
    description: StrictStr | None = None
    provider: StrictStr | None = None
    category: StrictStr | None = None
    url: StrictStr | None = None
