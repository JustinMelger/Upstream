"""Activity feed page for shared/recommended notifications."""

from __future__ import annotations

from datetime import timezone
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.services.notifications_service import load_activity_feed


def _format_when(value: Any) -> str:
    dt = parse_iso_datetime(value)
    if dt is None:
        return str(value or "")
    return dt.astimezone(timezone.utc).strftime("%b %d, %Y %H:%M UTC")


def _target_url(target_type: str, target_id: int) -> str:
    if target_type == "course":
        return f"/courses?course_id={int(target_id)}"
    if target_type == "path":
        return f"/paths?path_id={int(target_id)}"
    if target_type == "article":
        return "/articles"
    return "/learning"


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/activity` route."""

    @ui.page("/activity")
    async def activity_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return

        render_shell(title="Activity", store=store, api=api)

        with render_container():
            request = getattr(ui.context.client, "request", None)
            query_params = getattr(request, "query_params", {}) if request is not None else {}
            initial_tab = str(getattr(query_params, "get", lambda _k, _d=None: _d)("tab", "inbox") or "").strip().lower()
            if initial_tab not in {"inbox", "team"}:
                initial_tab = "inbox"

            events: list[dict[str, Any]] = []

            with ui.row().classes("items-center justify-between w-full"):
                tab_filter = (
                    ui.radio({"inbox": "Inbox", "team": "Team activity"}, value=initial_tab)
                    .props("inline dense")
                    .classes("text-sm")
                )
                refresh_btn = ui.button("Refresh").props("dense outline")

            @ui.refreshable
            def activity_list() -> None:
                current_tab = str(tab_filter.value or "inbox")
                if not events:
                    with ui.card().classes("lp-card w-full"):
                        ui.label("No activity yet.").classes("text-base")
                        if current_tab == "team":
                            ui.label("When teammates share, recommend, or rate content, updates will appear here.").classes(
                                "text-sm"
                            ).style("color: var(--lp-muted)")
                        else:
                            ui.label(
                                "When teammates review or recommend your shared content, updates will appear here."
                            ).classes("text-sm").style("color: var(--lp-muted)")
                    return

                with ui.column().classes("w-full gap-3"):
                    for row in events:
                        message = str(row.get("message") or "").strip()
                        actor = str(row.get("actor") or "").strip()
                        created_at = str(row.get("created_at") or "").strip()
                        target_type = str(row.get("target_type") or "").strip()
                        target_label = str(row.get("target_label") or "").strip()
                        target_id = int(row.get("target_id") or 0)
                        with ui.card().classes("lp-card w-full"):
                            with ui.row().classes("items-center justify-between w-full"):
                                ui.label(message or "Activity update").classes("text-sm")
                                ui.label(_format_when(created_at)).classes("text-xs").style("color: var(--lp-muted)")
                            with ui.row().classes("items-center justify-between w-full mt-2"):
                                meta = actor
                                if target_label:
                                    meta = f"{meta} · {target_label}" if meta else target_label
                                ui.label(meta).classes("text-xs").style("color: var(--lp-muted)")
                                ui.button(
                                    "Open",
                                    on_click=lambda t=target_type, tid=target_id: ui.navigate.to(_target_url(t, tid)),
                                ).props("dense outline")

            @guard_ui_action(title="Load activity failed")
            async def _load() -> None:
                nonlocal events
                current_tab = str(tab_filter.value or "inbox")
                scope = "team" if current_tab == "team" else "inbox"
                events = await load_activity_feed(api=api, limit=50, scope=scope)
                activity_list.refresh()

            @guard_ui_action(title="Switch tab failed")
            async def _on_tab_change(*_args: Any) -> None:
                current = str(tab_filter.value or "inbox")
                ui.navigate.to(f"/activity?tab={current}")
                await _load()

            tab_filter.on("update:model-value", _on_tab_change)
            refresh_btn.on_click(_load)
            activity_list()
            await _load()
