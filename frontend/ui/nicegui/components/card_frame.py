"""Shared card frame primitives for consistent card layout structure."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from typing import Iterator

from nicegui import ui


@contextmanager
def render_card_topright() -> Iterator[None]:
    """Render a standardized top-right slot for badges/overflow actions."""
    with ui.element("div").classes("lp-card-topright"):
        yield


@contextmanager
def render_card_main_row(*, classes: str = "") -> Iterator[None]:
    """Render a standardized main row for card content/media."""
    row_classes = "lp-card-main no-wrap"
    if str(classes or "").strip():
        row_classes = f"{row_classes} {classes.strip()}"
    with ui.row().classes(row_classes):
        yield


@contextmanager
def render_card_content_column(*, classes: str = "") -> Iterator[None]:
    """Render a standardized content column used by all cards."""
    col_classes = "lp-card-content"
    if str(classes or "").strip():
        col_classes = f"{col_classes} {classes.strip()}"
    with ui.column().classes(col_classes):
        yield


def render_card_actions_row(*, render_actions: Callable[[], None], classes: str = "") -> None:
    """Render a standardized bottom action row for cards."""
    with ui.row().classes("items-center gap-2 mt-2") as actions_row:
        actions_row.classes("lp-card-actions")
        if str(classes or "").strip():
            actions_row.classes(classes.strip())
        render_actions()
