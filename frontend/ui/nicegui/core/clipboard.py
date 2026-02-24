"""Clipboard helpers for NiceGUI pages."""

from __future__ import annotations

import json

from nicegui import ui

from frontend.ui.nicegui.core.errors import safe_notify


def copy_text_to_clipboard(*, text: str, success_message: str = "Link copied") -> None:
    """Copy text to browser clipboard and show a success toast."""
    ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(str(text or ''))});")
    safe_notify(str(success_message), type="positive")
