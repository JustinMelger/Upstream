"""Global theme customization for the NiceGUI frontend.

NiceGUI uses Quasar components. Global CSS must be registered with
`shared=True` when using `@ui.page` routes so it applies across all pages.
"""

from __future__ import annotations

from pathlib import Path

from nicegui import ui


_THEME_CSS_PATHS = (
    Path(__file__).with_name("theme").joinpath("foundation.css"),
    Path(__file__).with_name("theme").joinpath("home.css"),
    Path(__file__).with_name("theme").joinpath("features.css"),
)
_FONT_HEAD_HTML = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
"""


def apply_theme() -> None:
    """Apply the global design-token based theme for the NiceGUI app."""
    ui.add_head_html(_FONT_HEAD_HTML, shared=True)
    ui.add_css("\n".join(path.read_text(encoding="utf-8") for path in _THEME_CSS_PATHS), shared=True)
