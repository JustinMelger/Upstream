"""Validate edits shared by article and video services."""

from urllib.parse import urlsplit

from backend.core.errors import ServiceError
from backend.services.recommendation_notes import normalize_note


def validate_content_edit(payload: dict, *, kind: str) -> dict:
    """Preserve absent fields and reject empty required values or unsafe URLs."""
    allowed = {"title", "url", "recommendation_note"} | (
        {"tags", "description"} if kind == "article" else {"description", "provider", "category"}
    )
    values = {key: value for key, value in payload.items() if key in allowed}
    for key in ("title", "url"):
        if key in values:
            value = str(values[key] or "").strip()
            if not value:
                raise ServiceError(detail=f"missing_{key}", status_code=400)
            values[key] = value
    if "url" in values:
        parsed = urlsplit(values["url"])
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ServiceError(detail="invalid_url", status_code=400)
    if "recommendation_note" in values:
        values["recommendation_note"] = normalize_note(values["recommendation_note"])
    if "description" in values:
        values["description"] = (
            normalize_article_description(values["description"]) if kind == "article" else values["description"] or ""
        )
    return values


def normalize_article_description(value: str | None) -> str | None:
    """Normalize optional article summaries without touching existing video rules."""
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > 2000:
        raise ServiceError(detail="invalid_description", status_code=422)
    return value.strip() or None
