"""Pure helpers for the dedicated learning-item share page."""

from __future__ import annotations

from frontend.ui.nicegui.core.learning_items import (
    infer_learning_item_type,
    learning_item_type_label,
    normalize_learning_item_type,
)


def normalize_requested_share_type(value: str) -> str:
    """Normalize the requested `/share/item?type=` value."""
    return normalize_learning_item_type(value, default="course")


def share_route_for_type(item_type: str) -> str:
    """Build the canonical `/share/item` route for one subtype."""
    normalized = normalize_requested_share_type(item_type)
    return f"/share/item?type={normalized}"


def share_subtitle_for_type(item_type: str) -> str:
    """Return page subtitle text for one subtype."""
    normalized = normalize_requested_share_type(item_type)
    if normalized == "video":
        return "Share a video others should learn from."
    if normalized == "article":
        return "Share a useful article for others to discover."
    return "Share a course others should learn from."


def share_title_input_label(item_type: str) -> str:
    """Return the title-field label for one subtype."""
    normalized = normalize_requested_share_type(item_type)
    return f"{learning_item_type_label(normalized)} title"


def share_detected_type_text(*, current_type: str, source_url: str, suggested_type: str = "") -> str:
    """Return the inline detected-type hint for the share page."""
    normalized_current = normalize_requested_share_type(current_type)
    detected = normalize_learning_item_type(
        suggested_type or infer_learning_item_type(url=source_url, fallback="article"),
        default="article",
    )
    if not str(source_url or "").strip():
        return ""
    detected_label = learning_item_type_label(detected)
    current_label = learning_item_type_label(normalized_current)
    if detected == normalized_current:
        return f"Detected type: {detected_label}."
    return f"Detected type: {detected_label}. Current selection: {current_label}."


def validate_course_like_publish(*, item_type: str, title: str, description: str, url: str) -> str | None:
    """Validate publish requirements for course-backed item types."""
    normalized = normalize_requested_share_type(item_type)
    label = learning_item_type_label(normalized)
    if not str(title or "").strip():
        return f"{label} title is required"
    if not str(description or "").strip():
        return "Description is required"
    if not str(url or "").strip():
        return "Valid learning item URL is required"
    return None
