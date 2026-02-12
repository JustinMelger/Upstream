"""Dashboard (home) page for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore


def _format_time(ts: str | None) -> str:
    """Format an ISO-8601 timestamp into a short date-time string.

    Args:
        ts: ISO-8601 timestamp string.

    Returns:
        A human-friendly local-time string, or the original string if parsing fails.
    """
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %H:%M")
    except ValueError:
        return ts


def _format_date(ts: str | None) -> str:
    """Format an ISO-8601 timestamp into a short date string.

    Args:
        ts: ISO-8601 timestamp string.

    Returns:
        A human-friendly local-date string, or the original string if parsing fails.
    """
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return ts


def _parse_iso_ts(ts: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp into a datetime.

    Args:
        ts: ISO-8601 timestamp string (optionally with `Z`).

    Returns:
        Parsed datetime, or None if parsing fails.
    """
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def _course_title_by_id(courses: list[dict[str, Any]]) -> dict[int, str]:
    """Build a mapping of course_id -> course_title."""
    out: dict[int, str] = {}
    for c in courses:
        cid = c.get("id")
        if cid is None:
            continue
        try:
            out[int(cid)] = str(c.get("title") or "")
        except (TypeError, ValueError):
            continue
    return out


def _tracking_map(tracking_rows: list[dict[str, Any]]) -> dict[int, str]:
    """Build a mapping of course_id -> status."""
    out: dict[int, str] = {}
    for r in tracking_rows:
        try:
            cid = int(r.get("course_id") or 0)
        except (TypeError, ValueError):
            continue
        out[cid] = str(r.get("status") or "")
    return out


def _ids_by_status(tracking: dict[int, str]) -> tuple[list[int], list[int], list[int]]:
    """Split a tracking map into lists of course IDs for each status."""
    interested = [cid for cid, st in tracking.items() if st == "interested"]
    in_progress = [cid for cid, st in tracking.items() if st == "in_progress"]
    completed = [cid for cid, st in tracking.items() if st == "completed"]
    return interested, in_progress, completed


def _recent_tracking(tracking_rows: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    """Return most recently updated tracking rows."""

    def _key(r: dict[str, Any]) -> float:
        dt = _parse_iso_ts(str(r.get("updated_at") or ""))
        return dt.timestamp() if dt else 0.0

    return sorted(tracking_rows, key=_key, reverse=True)[:limit]


def _recent_courses(courses: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    """Return most recently created courses."""

    def _key(c: dict[str, Any]) -> float:
        dt = _parse_iso_ts(str(c.get("created_at") or ""))
        return dt.timestamp() if dt else 0.0

    return sorted(courses, key=_key, reverse=True)[:limit]


async def _load_dashboard_data(
    *,
    api: ApiClient,
    username: str,
    is_admin: bool,
    mode_value: str,
) -> dict[str, Any]:
    """Load all dashboard data required for the page.

    Args:
        api: API client.
        username: Current username.
        is_admin: Whether the current user is an admin.
        mode_value: Either "mine" or "team".

    Returns:
        A dict containing the datasets needed by the dashboard.
    """
    tasks: list[asyncio.Future[Any] | asyncio.Task[Any]] = [
        asyncio.create_task(api.get("/courses")),
        asyncio.create_task(api.get("/paths")),
        asyncio.create_task(api.get("/paths/selected/list")),
        asyncio.create_task(api.get("/tracking")),
    ]

    # Stats snapshot
    if is_admin and mode_value == "team":
        tasks.append(asyncio.create_task(api.get("/tracking/stats")))
    else:
        tasks.append(asyncio.create_task(api.get("/tracking/stats", params={"colleague_id": username})))

    # Admin-only panels
    if is_admin:
        tasks.append(asyncio.create_task(api.get("/tracking/stats/users")))
        tasks.append(asyncio.create_task(api.get("/tracking/recent", params={"limit": 5})))

    results = await asyncio.gather(*tasks)
    idx = 0
    courses = list(results[idx] or [])
    idx += 1
    paths = list(results[idx] or [])
    idx += 1
    selected_paths = list(results[idx] or [])
    idx += 1
    tracking_rows = list(results[idx] or [])
    idx += 1
    snapshot_stats = dict(results[idx] or {})
    idx += 1

    team_stats_by_user: list[dict[str, Any]] = []
    team_recent: list[dict[str, Any]] = []
    if is_admin:
        team_stats_by_user = list(results[idx] or [])
        idx += 1
        team_recent = list(results[idx] or [])
        idx += 1

    return {
        "courses": courses,
        "paths": paths,
        "selected_paths": selected_paths,
        "tracking_rows": tracking_rows,
        "snapshot_stats": snapshot_stats,
        "team_stats_by_user": team_stats_by_user,
        "team_recent": team_recent,
    }


async def _load_path_detail(*, api: ApiClient, path_id: int) -> dict[str, Any] | None:
    """Load a single path including its courses."""
    try:
        return await api.get(f"/paths/{path_id}")
    except Exception:
        return None


def _render_snapshot_metrics(*, snapshot_stats: dict[str, int]) -> None:
    """Render the three dashboard snapshot metric cards."""

    def _metric(label: str, value: int, cls: str) -> None:
        with ui.card().classes("lp-card grow"):
            ui.label(label).classes("text-sm text-gray-600")
            ui.label(str(value)).classes(f"text-3xl font-semibold {cls}")

    ui.label("Progress snapshot").classes("text-lg font-semibold mt-2")
    with ui.row().classes("w-full gap-3"):
        _metric("Interested", int(snapshot_stats.get("interested", 0)), "")
        _metric("In progress", int(snapshot_stats.get("in_progress", 0)), "")
        _metric("Completed", int(snapshot_stats.get("completed", 0)), "")


def _render_course_list_card(*, title: str, ids: list[int], title_by_id: dict[int, str]) -> None:
    """Render a card of course bullets."""
    with ui.card().classes("lp-card w-full"):
        ui.label(title).classes("text-md font-semibold")
        if not ids:
            ui.label("No courses yet.").classes("text-sm text-gray-600")
            return
        for cid in ids[:8]:
            ui.label(f"• {title_by_id.get(cid) or f'Course {cid}'}").classes("text-sm")


def _render_selected_path_progress_cards(
    *,
    path_details: list[dict[str, Any]],
    tracking: dict[int, str],
) -> None:
    """Render path progress cards for the user's selected paths.

    Note:
        This function is intentionally synchronous. NiceGUI UI elements must be
        created within the page's active slot; do not call UI code from
        background tasks.
    """
    for detail in path_details:
        courses_in_path = list(detail.get("courses") or [])
        total = len(courses_in_path)
        completed = sum(1 for c in courses_in_path if tracking.get(int(c.get("id") or 0), "") == "completed")
        in_prog = sum(1 for c in courses_in_path if tracking.get(int(c.get("id") or 0), "") == "in_progress")
        intr = sum(1 for c in courses_in_path if tracking.get(int(c.get("id") or 0), "") == "interested")
        progress = (completed / total) if total else 0.0

        with ui.card().classes("lp-card w-full"):
            ui.label(detail.get("name") or "(untitled path)").classes("text-md font-semibold")
            ui.linear_progress(progress, show_value=False).classes("w-full")
            ui.label(f"Progress: {completed}/{total} completed • In progress: {in_prog} • Interested: {intr}").classes(
                "text-sm text-gray-600"
            )


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/` route (dashboard).

    Args:
        store: Session store.
        api: API client.
    """

    @ui.page("/")
    async def home_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return
        username = str(user.get("username") or "")
        role = str(user.get("role") or "user")
        is_admin = role == "admin"

        render_shell(title="Dashboard", store=store, api=api)
        with render_container():
            ui.label("Your learning overview and recent activity.").classes("text-sm text-gray-600")

            # State
            courses: list[dict[str, Any]] = []
            paths: list[dict[str, Any]] = []
            selected_paths: list[dict[str, Any]] = []
            selected_path_details: list[dict[str, Any]] = []
            tracking_rows: list[dict[str, Any]] = []
            snapshot_stats: dict[str, int] = {}
            team_recent: list[dict[str, Any]] = []
            team_stats_by_user: list[dict[str, Any]] = []

            meta = ui.label("").classes("text-sm text-gray-600")
            loading = False

            mode = None
            if is_admin:
                mode = ui.radio({"mine": "My stats", "team": "Team totals"}, value="mine")

            async def _load() -> None:
                nonlocal courses, paths, selected_paths, tracking_rows, snapshot_stats, team_recent, team_stats_by_user
                nonlocal selected_path_details
                nonlocal loading
                if loading:
                    return
                loading = True
                refresh_btn.disable()
                meta.text = "Loading..."

                try:
                    data = await _load_dashboard_data(
                        api=api,
                        username=username,
                        is_admin=is_admin,
                        mode_value=str(mode.value) if mode is not None else "mine",
                    )
                    courses = list(data["courses"])
                    paths = list(data["paths"])
                    selected_paths = list(data["selected_paths"])
                    tracking_rows = list(data["tracking_rows"])
                    snapshot_stats = dict(data["snapshot_stats"])
                    team_stats_by_user = list(data["team_stats_by_user"])
                    team_recent = list(data["team_recent"])

                    # Prefetch path detail for progress cards (limit to 5).
                    tracking = _tracking_map(tracking_rows)
                    shown = selected_paths[:5]
                    details = await asyncio.gather(
                        *[(_load_path_detail(api=api, path_id=int(p.get("id") or 0))) for p in shown]
                    )
                    selected_path_details = [d for d in details if d]

                    dashboard.refresh()
                    meta.text = "Updated"
                except Exception as exc:  # ApiError already stringifies nicely, but keep this generic.
                    ui.notify(str(exc), type="negative")
                    courses = []
                    paths = []
                    selected_paths = []
                    selected_path_details = []
                    tracking_rows = []
                    snapshot_stats = {}
                    team_recent = []
                    team_stats_by_user = []
                    dashboard.refresh()
                    meta.text = "Failed to load"
                finally:
                    loading = False
                    refresh_btn.enable()

            @ui.refreshable
            def dashboard() -> None:
                tracking = _tracking_map(tracking_rows)
                title_by_id = _course_title_by_id(courses)

                # Progress snapshot
                _render_snapshot_metrics(snapshot_stats=snapshot_stats)

                ui.separator()

                # Course lists by status
                ui.label("My courses by status").classes("text-lg font-semibold")
                interested_ids, in_progress_ids, completed_ids = _ids_by_status(tracking)

                with ui.row().classes("w-full gap-3"):
                    _render_course_list_card(title="Interested", ids=interested_ids, title_by_id=title_by_id)
                    _render_course_list_card(title="In progress", ids=in_progress_ids, title_by_id=title_by_id)
                    _render_course_list_card(title="Completed", ids=completed_ids, title_by_id=title_by_id)

                ui.separator()

                # My path progress
                ui.label("My path progress").classes("text-lg font-semibold")
                if not selected_paths:
                    ui.label("No paths selected yet.").classes("text-sm text-gray-600")
                else:
                    _render_selected_path_progress_cards(path_details=selected_path_details, tracking=tracking)

                ui.separator()

                # Recent activity (user-local: sort tracking rows)
                ui.label("Recent activity").classes("text-lg font-semibold")
                if is_admin:
                    ui.label("Your recent updates are shown below; team activity is in the admin section.").classes(
                        "text-sm text-gray-600"
                    )

                recent = _recent_tracking(tracking_rows, limit=3)
                if not recent:
                    ui.label("No recent updates yet.").classes("text-sm text-gray-600")
                else:
                    with ui.card().classes("lp-card w-full"):
                        for item in recent:
                            cid = int(item.get("course_id") or 0)
                            title = title_by_id.get(cid) or f"Course {cid}"
                            status = str(item.get("status") or "")
                            updated = _format_time(str(item.get("updated_at") or ""))
                            ui.label(f"• {title} — {status} ({updated})").classes("text-sm")

                # Admin section
                if is_admin:
                    ui.separator()
                    ui.label("Team stats by user").classes("text-lg font-semibold")
                    if not team_stats_by_user:
                        ui.label("No user stats yet.").classes("text-sm text-gray-600")
                    else:
                        ui.table(
                            columns=[
                                {"name": "colleague_id", "label": "User", "field": "colleague_id"},
                                {"name": "interested", "label": "Interested", "field": "interested"},
                                {"name": "in_progress", "label": "In progress", "field": "in_progress"},
                                {"name": "completed", "label": "Completed", "field": "completed"},
                            ],
                            rows=team_stats_by_user,
                            row_key="colleague_id",
                        ).classes("w-full")

                    ui.label("Team recent activity").classes("text-lg font-semibold mt-4")
                    if not team_recent:
                        ui.label("No team activity yet.").classes("text-sm text-gray-600")
                    else:
                        with ui.card().classes("lp-card w-full"):
                            for item in team_recent:
                                cid = int(item.get("course_id") or 0)
                                who = str(item.get("colleague_id") or "someone")
                                title = title_by_id.get(cid) or f"Course {cid}"
                                status = str(item.get("status") or "")
                                updated = _format_time(str(item.get("updated_at") or ""))
                                ui.label(f"• {who}: {title} — {status} ({updated})").classes("text-sm")

                ui.separator()

                # Featured paths
                ui.label("Featured paths").classes("text-lg font-semibold")
                if not paths:
                    ui.label("No paths yet. Create one on the Paths page.").classes("text-sm text-gray-600")
                else:
                    with ui.card().classes("lp-card w-full"):
                        for p in paths[:3]:
                            ui.link(p.get("name") or "(untitled path)", "/paths")
                            if p.get("description"):
                                ui.label(str(p.get("description"))).classes("text-sm text-gray-600")
                            ui.separator()

                # Recently added courses
                ui.label("Recently added courses").classes("text-lg font-semibold mt-4")
                if not courses:
                    ui.label("No courses yet. Add one on the Courses page.").classes("text-sm text-gray-600")
                else:
                    recent_courses = _recent_courses(courses, limit=3)
                    with ui.card().classes("lp-card w-full"):
                        for c in recent_courses:
                            added = _format_date(str(c.get("created_at") or ""))
                            date_str = f" ({added})" if added else ""
                            ui.label(f"• {c.get('title') or ''} — {c.get('provider') or ''}{date_str}").classes("text-sm")

            with ui.row().classes("items-center justify-between w-full"):
                refresh_btn = ui.button("Refresh", on_click=_load).props("outline")
                ui.label(f"Signed in as {username} ({role})").classes("text-sm text-gray-600")
            meta

            if mode is not None:

                async def _on_mode_change(_: Any) -> None:
                    await _load()

                mode.on("update:model-value", _on_mode_change)

            await _load()
            dashboard()
