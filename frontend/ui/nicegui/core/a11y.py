"""Lightweight accessibility helpers for common UI controls."""

from __future__ import annotations

from typing import Any


def apply_icon_button_a11y(control: Any, *, label: str, tooltip: str | None = None) -> Any:
    """Attach ARIA label + tooltip to icon-only button-like controls."""
    aria_label = str(label or "").replace('"', "'").strip() or "Action"
    if hasattr(control, "props"):
        control.props(f'aria-label="{aria_label}"')
    if hasattr(control, "tooltip"):
        control.tooltip(str(tooltip or aria_label))
    return control
