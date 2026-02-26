from __future__ import annotations

from backend.api.schemas.common import APIModel


class UrlPreviewMetadataRequest(APIModel):
    """Request payload for URL metadata suggestions."""

    url: str


class UrlPreviewMetadataResponse(APIModel):
    """Resolved URL metadata and suggested form values."""

    source_url: str
    normalized_url: str
    title: str = ""
    description: str = ""
    site_name: str = ""
    preview_image_url: str = ""
    suggested_provider: str = ""
    suggested_category: str = ""
    suggested_tags: list[str] = []
