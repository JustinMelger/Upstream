"""Validation for an author's optional recommendation note."""

from backend.core.errors import ServiceError


def normalize_note(value: object) -> str | None:
    """Validate plain text and normalize empty notes without truncation."""
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > 1000:
        raise ServiceError(detail="invalid_recommendation_note", status_code=422)
    return value.strip() or None
