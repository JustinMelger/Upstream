"""Reusable catalog hero block for list pages."""

from __future__ import annotations

from nicegui import ui


def render_catalog_hero(*, eyebrow: str, title: str, subtitle: str) -> None:
    """Render a compact hero panel that introduces page intent."""
    with ui.element("section").classes("lp-catalog-hero"):
        if str(eyebrow or "").strip():
            ui.label(str(eyebrow)).classes("lp-catalog-hero-eyebrow")
        ui.label(str(title)).classes("lp-catalog-hero-title")
        if str(subtitle or "").strip():
            ui.label(str(subtitle)).classes("lp-catalog-hero-subtitle")
