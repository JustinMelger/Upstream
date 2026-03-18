"""Shared helpers for Explore dedicated detail pages."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_catalog_scope, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.paths.item_helpers import path_course_ids


def parse_detail_id(raw_id: str) -> int:
    """Parse route path id value; return 0 for invalid input."""
    try:
        return int(raw_id)
    except (TypeError, ValueError):
        return 0


def parse_view_mode() -> str:
    """Parse Explore detail view mode from query params."""
    request = getattr(ui.context.client, "request", None)
    query_params = getattr(request, "query_params", None)
    view = str((query_params or {}).get("view", "full") if query_params is not None else "full")
    return "reviews" if view == "reviews" else "full"


def render_breadcrumb(*, label: str) -> None:
    """Render standard Explore detail breadcrumb with close action."""
    with ui.row().classes("w-full items-center justify-between gap-2 text-xs lp-explore-detail-breadcrumb"):
        with ui.row().classes("items-center gap-2"):
            ui.link("Explore", "/explore")
            ui.label("›")
            ui.label(str(label or "Details"))
        ui.button("Close", icon="close", on_click=lambda: ui.navigate.to("/explore")).props("outline dense")


def render_detail_scope(*, store: SessionStore, api: ApiClient) -> Any:
    """Render shell + container for Explore detail pages."""
    render_shell(title="Explore", store=store, api=api)
    return render_catalog_scope(variant="explore").classes("lp-container lp-explore-detail")


def parse_path_course_ids(path_detail: dict[str, Any]) -> list[int]:
    """Parse path course ids from detail payload."""
    return path_course_ids(detail=path_detail)
