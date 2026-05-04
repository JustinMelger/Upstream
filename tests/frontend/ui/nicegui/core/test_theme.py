from __future__ import annotations

from frontend.ui.nicegui.core import theme


def test_theme_injects_static_css_links_and_nicegui_js_constants() -> None:
    css_head = "\n".join(
        f'<link rel="stylesheet" href="{theme._THEME_STATIC_URL}/{filename}">' for filename in theme._THEME_CSS_FILES
    )

    assert "/lp-static/theme/foundation.css" in css_head
