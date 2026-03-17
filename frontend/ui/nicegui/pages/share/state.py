"""Typed UI state models for dedicated learning-item share pages."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ShareCourseUiState:
    """Local UI-only state for `/share/item?type=course`."""

    latest_suggestions: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ShareArticleUiState:
    """Local UI-only state for `/share/item?type=article`."""

    latest_suggestions: dict[str, str] = field(default_factory=dict)
