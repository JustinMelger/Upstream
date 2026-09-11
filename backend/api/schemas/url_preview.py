from __future__ import annotations

from pydantic import Field, StrictStr

from backend.api.schemas.common import APIModel


class UrlPreviewMetadataRequest(APIModel):
    """Request payload for URL metadata suggestions."""

    url: StrictStr = Field(min_length=1, max_length=4096)


class UrlPreviewMetadataResponse(APIModel):
    """Resolved URL metadata and suggested form values."""

    source_url: str
    normalized_url: str
    suggested_learning_item_type: str = ""
    title: str = ""
    description: str = ""
    site_name: str = ""
    preview_image_url: str = ""
    suggested_provider: str = ""
    suggested_category: str = ""
    suggested_tags: list[str] = []
