"""Reusable dashboard section primitives."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager

from nicegui import ui


def render_section_header(*, title: str, description: str | None = None, classes: str = "") -> None:
    """Render a compact section header."""
    container_classes = f"w-full gap-1 lp-section-header {classes}".strip()
    with ui.column().classes(container_classes):
        ui.label(str(title or "")).classes("lp-section-title")
        if str(description or "").strip():
            ui.label(str(description or "")).classes("text-sm lp-section-description").style("color: var(--lp-muted)")


def render_metric_card(*, label: str, value: int | str, classes: str = "") -> None:
    """Render one compact dashboard metric card."""
    card_classes = f"lp-card lp-metric-card {classes}".strip()
    with ui.card().classes(card_classes):
        ui.label(str(label or "")).classes("lp-metric-label")
        ui.label(str(value)).classes("lp-metric-value")


@contextmanager
def render_dashboard_list_card(
    *,
    icon: str,
    title: str,
    subtitle: str,
    classes: str = "",
    render_actions: Callable[[], None] | None = None,
) -> Iterator[None]:
    """Render a compact dashboard list card with optional row actions."""
    card_classes = f"lp-track-card {classes}".strip()
    with ui.element("div").classes(card_classes):
        with ui.row().classes("w-full items-start justify-between gap-3 lp-track-head-row"):
            with ui.row().classes("items-start gap-2 lp-track-identity"):
                ui.icon(str(icon or "article")).classes("lp-track-avatar")
                with ui.column().classes("gap-0 lp-track-title-block"):
                    ui.label(str(title or "")).classes("text-sm font-semibold lp-track-title")
                    if str(subtitle or "").strip():
                        ui.label(str(subtitle or "")).classes("text-xs lp-home-track-meta")
            if render_actions is not None:
                with ui.row().classes("items-center gap-1 lp-track-actions lp-track-actions-group lp-shared-actions"):
                    render_actions()
        yield


@contextmanager
def render_content_list_section(*, title: str, empty_text: str, has_items: bool, classes: str = "") -> Iterator[bool]:
    """Render a titled content section and yield whether callers should render items."""
    section_classes = f"w-full gap-3 lp-content-list-section {classes}".strip()
    with ui.column().classes(section_classes):
        ui.label(str(title or "")).classes("lp-section-title")
        if not has_items:
            ui.label(str(empty_text or "")).classes("text-sm lp-empty-copy").style("color: var(--lp-muted)")
            yield False
            return
        yield True
