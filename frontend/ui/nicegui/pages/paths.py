"""Paths browse/admin page for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.card_actions import render_view_review_actions
from frontend.ui.nicegui.components.layout import render_container, render_shell, render_split_layout
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.owner_menu import render_owner_menu
from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel
from frontend.ui.nicegui.components.status_chips import (
    tracking_chip_class,
    tracking_label,
)
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.datetime_utils import is_recent, parse_iso_datetime
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.services.courses_service import index_tracking_by_course_id
from frontend.ui.nicegui.services.paths_service import (
    compute_path_progress,
    index_courses_by_int_id,
    index_rows_by_int_id,
    load_paths_page_data,
    select_path_and_seed_tracking,
)


_index_rows_by_int_id = index_rows_by_int_id
_index_courses_by_int_id = index_courses_by_int_id
_index_tracking_by_course_id = index_tracking_by_course_id


_parse_iso_datetime = parse_iso_datetime
_is_recent = is_recent


def _course_options(courses: list[dict[str, Any]] | None) -> dict[int, str]:
    """Convert courses into select options."""
    options: dict[int, str] = {}
    for c in list(courses or []):
        if not isinstance(c, dict) or c.get("id") is None:
            continue
        try:
            cid = int(c["id"])
        except (TypeError, ValueError):
            continue
        options[cid] = f"{c.get('title') or ''} (#{cid})"
    return options


def _filter_paths(paths: list[dict[str, Any]] | None, needle: str) -> list[dict[str, Any]]:
    """Filter paths by a lower-cased substring match on name/description."""
    if not needle:
        return list(paths or [])
    return [
        p
        for p in list(paths or [])
        if needle in str(p.get("name") or "").lower() or needle in str(p.get("description") or "").lower()
    ]


def _format_review_summary(row: dict[str, Any] | None) -> str:
    """Format a path review summary row into a compact label."""
    if not isinstance(row, dict):
        return ""
    try:
        count = int(row.get("review_count") or 0)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return ""
    try:
        avg = float(row.get("avg_rating") or 0.0)
    except (TypeError, ValueError):
        avg = 0.0
    return f"{avg:.1f}/5 ({count})"


def _format_rating_badge(row: dict[str, Any] | None) -> str:
    """Format a compact rating badge for path cards (e.g., '4.2/5 (12)')."""
    if not isinstance(row, dict):
        return ""
    try:
        count = int(row.get("review_count") or 0)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return ""
    try:
        avg = float(row.get("avg_rating") or 0.0)
    except (TypeError, ValueError):
        avg = 0.0
    return f"{avg:.1f}/5 ({count})"


def _path_tracking_label(is_tracked: bool) -> str:
    """Return path tracking label for cards/details."""
    return "Tracked" if is_tracked else "Not tracked"


def _path_tracking_chip_class(is_tracked: bool) -> str:
    """Return chip class for path tracking state."""
    return "lp-chip lp-chip--sky" if is_tracked else "lp-chip lp-chip--muted"


def _normalize_path_view_mode(view_mode: str | None) -> str:
    """Normalize dialog mode to `full` or `reviews`."""
    return "reviews" if str(view_mode or "").strip().lower() == "reviews" else "full"


def _path_matches_state(path_id: int, selected_by_id: dict[int, dict[str, Any]], state_filter: str) -> bool:
    """Return whether a path id matches a tracked-state filter."""
    key = str(state_filter or "").strip()
    is_tracked = int(path_id) in selected_by_id
    if not key:
        return True
    if key == "tracked":
        return is_tracked
    if key == "not_tracked":
        return not is_tracked
    return True


async def _load_paths_page_data(
    api: ApiClient,
) -> tuple[
    list[dict[str, Any]],
    dict[int, dict[str, Any]],
    list[dict[str, Any]],
    dict[int, dict[str, Any]],
]:
    """Compat shim: use the NiceGUI paths service layer."""
    return await load_paths_page_data(api=api)


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/paths` route.

    Args:
        store: Session store.
        api: API client.
    """

    @ui.page("/paths")
    async def paths_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return

        render_shell(title="Paths", store=store, api=api)
        username = str(user.get("username") or "")
        is_admin = str(user.get("role") or "") == "admin"

        paths: list[dict[str, Any]] = []
        selected_by_id: dict[int, dict[str, Any]] = {}
        selected_detail_by_path_id: dict[int, dict[str, Any]] = {}
        tracking_by_course_id: dict[int, dict[str, Any]] = {}
        courses: list[dict[str, Any]] = []
        course_by_id: dict[int, dict[str, Any]] = {}
        path_review_summary_by_id: dict[int, dict[str, Any]] = {}
        loading = False
        loaded_once = False
        page_size = 10
        visible_count = page_size

        async def _reload_selected() -> None:
            """Reload selected path rows (used after select/unselect/status updates)."""
            nonlocal selected_by_id
            try:
                selected_result = await api.get("/paths/selected/list")
            except ApiError as exc:
                ui.notify(str(exc), type="negative")
                selected_by_id = {}
                return
            selected_by_id = _index_rows_by_int_id(list(selected_result or []))

        async def _reload_tracking() -> None:
            """Reload the current user's tracking map (used to compute path progress)."""
            nonlocal tracking_by_course_id
            try:
                tracking_result = await api.get("/tracking")
            except ApiError:
                tracking_by_course_id = {}
                return
            tracking_by_course_id = _index_tracking_by_course_id(list(tracking_result or []))

        async def _reload_selected_details() -> None:
            """Reload path detail payloads for currently selected paths."""
            nonlocal selected_detail_by_path_id
            path_ids = sorted(int(pid) for pid in selected_by_id.keys())
            selected_detail_by_path_id = {}
            if not path_ids:
                return
            results = await asyncio.gather(*(api.get(f"/paths/{pid}") for pid in path_ids), return_exceptions=True)
            for pid, payload in zip(path_ids, results, strict=False):
                if isinstance(payload, Exception):
                    continue
                if isinstance(payload, dict):
                    selected_detail_by_path_id[int(pid)] = payload

        async def _ensure_selected_detail(path_id: int) -> None:
            """Ensure a selected path has a detail payload cached."""
            nonlocal selected_detail_by_path_id
            if int(path_id) in selected_detail_by_path_id:
                return
            try:
                detail = await api.get(f"/paths/{int(path_id)}")
            except ApiError:
                return
            if isinstance(detail, dict):
                selected_detail_by_path_id[int(path_id)] = detail

        @guard_ui_action(title="Select failed")
        async def _select(path_id: int) -> None:
            cached_detail = selected_detail_by_path_id.get(int(path_id))
            seeded, detail = await select_path_and_seed_tracking(
                api=api,
                path_id=int(path_id),
                tracking_by_course_id=tracking_by_course_id,
                cached_detail=cached_detail if isinstance(cached_detail, dict) else None,
            )
            await _reload_selected()
            if isinstance(detail, dict):
                selected_detail_by_path_id[int(path_id)] = detail
            else:
                await _ensure_selected_detail(path_id)
            if seeded > 0:
                await _reload_tracking()
            if scope_filter is not None:
                scope_filter.value = "selected"
                scope_filter.update()
            msg = "Path added to My learning"
            if seeded > 0:
                msg = f"{msg} · {seeded} course(s) set to Interested"
            ui.notify(msg, type="positive")
            paths_list.refresh()
            await _open_details(path_id)

        @guard_ui_action(title="Unselect failed")
        async def _unselect(path_id: int) -> None:
            await api.post(f"/paths/{path_id}/unselect", {})
            await _reload_selected()
            selected_detail_by_path_id.pop(int(path_id), None)
            paths_list.refresh()

        @guard_ui_action(title="Delete path failed")
        async def _delete_path(path_id: int) -> None:
            await api.delete(f"/paths/{path_id}")
            await _load_all()
            ui.notify("Path deleted", type="positive")

        async def _open_edit(*, path_id: int, detail: dict[str, Any], detail_dialog: ui.dialog | None) -> None:
            """Open an edit dialog for a path (owner/admin only, enforced by backend)."""
            ordered_course_ids: list[int] = [
                int(c.get("id")) for c in (detail.get("courses") or []) if isinstance(c, dict) and c.get("id") is not None
            ]

            with ui.dialog() as edit_dialog, ui.card().classes("lp-card lp-dialog w-[min(900px,95vw)]"):
                ui.label("Edit Path").classes("text-xl font-semibold")

                name = ui.input("Name", value=str(detail.get("name") or "")).props("clearable").classes("w-full")
                description = (
                    ui.textarea("Description", value=str(detail.get("description") or "")).props("autogrow").classes("w-full")
                )

                ui.separator()
                ui.label("Course Order").classes("text-lg font-semibold")

                add_course = ui.select(
                    {cid: f"{c.get('title') or ''} (#{cid})" for cid, c in sorted(course_by_id.items())},
                    label="Add course",
                ).classes("w-full")

                async def _add_course() -> None:
                    try:
                        cid = int(add_course.value)
                    except (TypeError, ValueError):
                        return
                    if cid not in ordered_course_ids:
                        ordered_course_ids.append(cid)
                        courses_list.refresh()

                ui.button("Add", on_click=_add_course).props("outline")

                @ui.refreshable
                def courses_list() -> None:
                    with ui.column().classes("w-full gap-2"):
                        if not ordered_course_ids:
                            ui.label("No courses selected.").classes("text-sm text-gray-600")
                        for idx, cid in enumerate(list(ordered_course_ids)):
                            c = course_by_id.get(cid) or {}
                            title = str(c.get("title") or f"Course #{cid}")
                            with ui.row().classes("items-center justify-between"):
                                ui.label(f"{idx + 1}. {title}").classes("text-sm")
                                with ui.row().classes("items-center"):

                                    def _move_up(_idx: int = idx) -> None:
                                        if _idx <= 0:
                                            return
                                        ordered_course_ids[_idx - 1], ordered_course_ids[_idx] = (
                                            ordered_course_ids[_idx],
                                            ordered_course_ids[_idx - 1],
                                        )
                                        courses_list.refresh()

                                    def _move_down(_idx: int = idx) -> None:
                                        if _idx >= len(ordered_course_ids) - 1:
                                            return
                                        ordered_course_ids[_idx + 1], ordered_course_ids[_idx] = (
                                            ordered_course_ids[_idx],
                                            ordered_course_ids[_idx + 1],
                                        )
                                        courses_list.refresh()

                                    def _remove(_cid: int = cid) -> None:
                                        if _cid in ordered_course_ids:
                                            ordered_course_ids.remove(_cid)
                                            courses_list.refresh()

                                    ui.button("Up", on_click=_move_up).props("dense outline")
                                    ui.button("Down", on_click=_move_down).props("dense outline")
                                    ui.button("Remove", on_click=_remove).props("dense color=negative outline")

                courses_list()

                with ui.row().classes("justify-end mt-4"):

                    @guard_ui_action(title="Save changes failed")
                    async def _save() -> None:
                        payload = {
                            "name": str(name.value or ""),
                            "description": str(description.value or ""),
                            "course_ids": ordered_course_ids,
                        }
                        await api.put(f"/paths/{path_id}", payload)
                        await _load_all()
                        paths_list.refresh()
                        ui.notify("Path updated", type="positive")
                        edit_dialog.close()
                        if detail_dialog is not None:
                            detail_dialog.close()

                    ui.button("Save", on_click=_save)
                    ui.button("Cancel", on_click=edit_dialog.close).props("outline")

            edit_dialog.open()

        @guard_ui_action(title="Load path details failed")
        async def _open_details(path_id: int, *, view_mode: str = "full") -> None:
            """Open a path dialog.

            Args:
                path_id: Path ID.
                view_mode: Either "full" or "reviews".
            """
            detail = await api.get(f"/paths/{path_id}")
            normalized_view_mode = _normalize_path_view_mode(view_mode)
            path_reviews: list[dict[str, Any]] = []
            try:
                reviews_result = await api.get(f"/paths/{path_id}/reviews")
                path_reviews = [r for r in list(reviews_result or []) if isinstance(r, dict)]
            except ApiError:
                path_reviews = []

            courses_rows = list((detail.get("courses") or []) if isinstance(detail, dict) else [])
            completed, total_courses, progress = compute_path_progress(
                detail=detail if isinstance(detail, dict) else {},
                tracking_by_course_id=tracking_by_course_id,
            )
            course_ids_in_path: list[int] = []
            for c in courses_rows:
                if not isinstance(c, dict):
                    continue
                try:
                    cid = int(c.get("id") or 0)
                except (TypeError, ValueError):
                    continue
                if cid > 0:
                    course_ids_in_path.append(cid)

            review_summary_by_course_id: dict[int, dict[str, Any]] = {}
            if course_ids_in_path:
                try:
                    rows = await api.get("/courses/reviews/summary", params={"course_ids": course_ids_in_path})
                    for r in list(rows or []):
                        if not isinstance(r, dict):
                            continue
                        try:
                            cid = int(r.get("course_id") or 0)
                        except (TypeError, ValueError):
                            continue
                        if cid > 0:
                            review_summary_by_course_id[cid] = r
                except ApiError:
                    review_summary_by_course_id = {}

            def _summary_label(cid: int) -> str:
                row = review_summary_by_course_id.get(int(cid))
                if not isinstance(row, dict):
                    return ""
                try:
                    count = int(row.get("review_count") or 0)
                except (TypeError, ValueError):
                    count = 0
                if count <= 0:
                    return ""
                try:
                    avg = float(row.get("avg_rating") or 0.0)
                except (TypeError, ValueError):
                    avg = 0.0
                return f"{avg:.1f}/5 ({count})"

            def _course_tracking_status(cid: int) -> str:
                return str((tracking_by_course_id.get(int(cid)) or {}).get("status") or "").strip()

            courses_rows = [
                dict(
                    c,
                    reviews=_summary_label(int(c.get("id") or 0)),
                    tracking_status=_course_tracking_status(int(c.get("id") or 0)),
                )
                for c in courses_rows
                if isinstance(c, dict)
            ]

            next_course: dict[str, Any] | None = None
            for c in courses_rows:
                try:
                    cid = int(c.get("id") or 0)
                except (TypeError, ValueError):
                    continue
                if str((tracking_by_course_id.get(cid) or {}).get("status") or "") != "completed":
                    next_course = c
                    break

            with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(900px,95vw)]"):
                ui.label(detail.get("name") or "").classes("text-xl font-semibold")
                ui.label(detail.get("description") or "").classes("text-sm text-gray-600")
                summary = _format_review_summary(path_review_summary_by_id.get(int(path_id)))
                if summary:
                    ui.label(f"Reviews: {summary}").classes("text-sm").style("color: var(--lp-muted)")
                if normalized_view_mode != "reviews":
                    if total_courses > 0:
                        ui.label(f"Progress: {completed}/{total_courses} completed").classes("text-sm").style(
                            "color: var(--lp-muted)"
                        )
                        ui.linear_progress(progress, show_value=False).classes("w-full")

                    is_tracked = int(path_id) in selected_by_id
                    ui.label(f"State: {_path_tracking_label(is_tracked)}").classes("text-sm")

                    with ui.row().classes("items-center gap-2"):
                        if next_course is not None:

                            @guard_ui_action(title="Open next course failed")
                            async def _open_next() -> None:
                                url = str(next_course.get("url") or "").strip()
                                if url:
                                    ui.navigate.to(url, new_tab=True)
                                    return
                                ui.notify("Next course has no URL yet", type="warning")

                            cta = "Continue path" if completed > 0 else "Start next course"
                            ui.button(cta, on_click=_open_next).props("outline")
                        elif total_courses > 0:
                            ui.label("Path completed").classes("lp-chip lp-chip--lime")

                    ui.label("Courses").classes("text-lg font-semibold mt-4")
                    if not courses_rows:
                        ui.label("No courses in this path yet.").classes("text-sm").style("color: var(--lp-muted)")
                    else:
                        with ui.column().classes("w-full gap-2"):
                            for idx, course in enumerate(courses_rows, start=1):
                                title = str(course.get("title") or "").strip() or f"Course #{int(course.get('id') or 0)}"
                                provider = str(course.get("provider") or "").strip()
                                category = str(course.get("category") or "").strip()
                                reviews = str(course.get("reviews") or "").strip()
                                with ui.card().classes("w-full lp-card"):
                                    ui.label(f"{idx}. {title}").classes("font-medium")
                                    with ui.row().classes("items-center gap-2 flex-wrap"):
                                        if provider:
                                            ui.label(provider).classes("lp-chip lp-chip--subtle")
                                        if category:
                                            ui.label(category).classes("lp-chip lp-chip--subtle")
                                        if reviews:
                                            ui.label(reviews).classes("lp-chip lp-chip--subtle")
                                        ui.label(tracking_label(str(course.get("tracking_status") or ""))).classes(
                                            tracking_chip_class(str(course.get("tracking_status") or ""))
                                        )

                ui.separator().classes("my-2")

                def _sync_path_summary(current_reviews: list[dict[str, Any]]) -> None:
                    ratings: list[int] = []
                    for r in list(current_reviews or []):
                        try:
                            ratings.append(int(r.get("rating") or 0))
                        except (TypeError, ValueError):
                            continue
                    if not ratings:
                        path_review_summary_by_id[int(path_id)] = {
                            "path_id": int(path_id),
                            "avg_rating": 0.0,
                            "review_count": 0,
                        }
                    else:
                        avg = float(sum(ratings)) / float(len(ratings))
                        path_review_summary_by_id[int(path_id)] = {
                            "path_id": int(path_id),
                            "avg_rating": float(avg),
                            "review_count": int(len(ratings)),
                        }
                    paths_list.refresh()

                async def _save_path_review(rating: int, text: str) -> dict[str, Any]:
                    return await api.post(
                        f"/paths/{path_id}/reviews",
                        {
                            "rating": int(rating),
                            "text": str(text or ""),
                        },
                    )

                async def _delete_path_review(review_id: int) -> bool:
                    await api.delete(f"/paths/{path_id}/reviews/{int(review_id)}")
                    return True

                render_reviews_panel(
                    username=username,
                    is_admin=is_admin,
                    reviews=path_reviews,
                    section_title="Path reviews",
                    empty_text="No path reviews yet.",
                    on_save=_save_path_review,
                    on_delete=_delete_path_review,
                    on_changed=_sync_path_summary,
                )

                with ui.row().classes("justify-end mt-4"):
                    ui.button("Close", on_click=dialog.close).props("outline")

            dialog.open()

        with render_container():
            # Rail filters.
            status_filter: Any = None
            refresh_btn: Any = None
            sort_filter: Any = None
            scope_filter: Any = None

            # Share/create dialog (pre-built so opening is instant).
            create_dialog = ui.dialog()
            with create_dialog, ui.card().classes("lp-card lp-dialog w-[min(800px,95vw)]"):
                ui.label("Share Path").classes("text-xl font-semibold")
                create_name = ui.input("Name").props("clearable").classes("w-full")
                create_description = ui.textarea("Description").props("autogrow").classes("w-full")
                create_course_ids = ui.select({}, label="Courses (ordered)", multiple=True).classes("w-full")

                with ui.row().classes("justify-end mt-4"):

                    @guard_ui_action(title="Create path failed")
                    async def _create_submit() -> None:
                        payload = {
                            "name": str(create_name.value or ""),
                            "description": str(create_description.value or ""),
                            "course_ids": list(create_course_ids.value or []),
                        }
                        await api.post("/paths", payload)
                        ui.notify("Path created", type="positive")
                        create_dialog.close()
                        await _load_all()

                    ui.button("Share", on_click=_create_submit)
                    ui.button("Cancel", on_click=create_dialog.close).props("outline")

            def _open_create_dialog() -> None:
                create_name.value = ""
                create_description.value = ""
                create_course_ids.value = []
                create_dialog.open()

            # Top bar (search + primary action + sort + count).
            request = getattr(ui.context.client, "request", None)
            query_params = getattr(request, "query_params", {}) if request is not None else {}
            initial_tab = str(getattr(query_params, "get", lambda _k, _d=None: _d)("tab", "") or "").strip().lower()
            initial_scope = "selected" if initial_tab == "selected" else "all"

            with ui.row().classes("lp-topbar"):
                q = ui.input("Search paths").props("clearable debounce=300").style("flex: 1")
                with ui.row().classes("items-center gap-2").style("margin-left: auto"):
                    ui.button("Share", on_click=_open_create_dialog).props("dense")
                    scope_filter = (
                        ui.radio(
                            {"all": "All", "selected": "Selected"},
                            value=initial_scope,
                        )
                        .props("inline dense")
                        .classes("text-sm")
                    )
                    sort_filter = (
                        ui.select(
                            {
                                "": "Recommended",
                                "top_rated": "Top rated",
                                "most_reviewed": "Most reviewed",
                                "newest": "Recently added",
                                "name_az": "Name A–Z",
                            },
                            value="",
                            label=None,
                        )
                        .props("dense")
                        .style("min-width: 180px")
                    )
                    meta = ui.label("").classes("lp-topbar-meta")

            def _status_key(pid: int) -> str:
                return "tracked" if int(pid) in selected_by_id else "not_tracked"

            def _recompute_facet_options() -> None:
                """Recompute status facet options with counts based on the current local filters."""
                if status_filter is None:
                    return
                scope_v = str(scope_filter.value or "all")
                needle = str(q.value or "").strip().lower()

                def _passes(p: dict[str, Any], *, ignore: str) -> bool:
                    if ignore != "scope" and scope_v == "selected":
                        pid = int(p.get("id") or 0)
                        if pid <= 0 or pid not in selected_by_id:
                            return False
                    if needle and ignore != "needle":
                        if (
                            needle not in str(p.get("name") or "").lower()
                            and needle not in str(p.get("description") or "").lower()
                        ):
                            return False
                    if ignore != "status":
                        status_v = str(status_filter.value or "").strip()
                        if status_v and not _path_matches_state(int(p.get("id") or 0), selected_by_id, status_v):
                            return False
                    return True

                counts: dict[str, int] = {"not_tracked": 0, "tracked": 0}
                for p in paths:
                    if not _passes(p, ignore="status"):
                        continue
                    pid = int(p.get("id") or 0)
                    counts[_status_key(pid)] = int(counts.get(_status_key(pid), 0)) + 1

                if scope_v == "selected":
                    status_filter.options = {
                        "": "Any state",
                        "tracked": f"Tracked ({counts.get('tracked', 0)})",
                    }
                else:
                    status_filter.options = {
                        "": "Any state",
                        "not_tracked": f"Not tracked ({counts.get('not_tracked', 0)})",
                        "tracked": f"Tracked ({counts.get('tracked', 0)})",
                    }
                if status_filter.value and status_filter.value not in status_filter.options:
                    status_filter.value = ""
                status_filter.update()

            def _refresh_list(*_: Any) -> None:
                nonlocal visible_count
                visible_count = page_size
                _recompute_facet_options()
                active_filters.refresh()
                paths_list.refresh()

            def _clear_filter_values() -> None:
                q.value = ""
                if status_filter is not None:
                    status_filter.value = ""
                sort_filter.value = ""
                scope_filter.value = "all"
                q.update()
                if status_filter is not None:
                    status_filter.update()
                sort_filter.update()
                scope_filter.update()
                _recompute_facet_options()
                active_filters.refresh()
                paths_list.refresh()

            @guard_ui_action(title="Reset filters failed")
            async def _reset_all() -> None:
                _clear_filter_values()
                await _load_all()

            q.on("update:model-value", _refresh_list)
            sort_filter.on("update:model-value", _refresh_list)
            scope_filter.on("update:model-value", _refresh_list)

            @ui.refreshable
            def active_filters() -> None:
                def _chip(label: str, on_clear: Any) -> None:
                    with ui.row().classes("items-center"):
                        with ui.element("div").classes("lp-filter-chip"):
                            ui.label(label)
                            ui.button("×", on_click=on_clear).props("dense flat")

                any_chip = False
                with ui.row().classes("items-center gap-2 w-full"):
                    if str(scope_filter.value or "") == "selected":
                        any_chip = True

                        def _clear_scope() -> None:
                            scope_filter.value = "all"
                            scope_filter.update()
                            _refresh_list()

                        _chip("View: Selected", _clear_scope)

                    if str(q.value or "").strip():
                        any_chip = True

                        def _clear_q() -> None:
                            q.value = ""
                            q.update()
                            _refresh_list()

                        _chip(f"Search: {str(q.value or '').strip()}", _clear_q)

                    if status_filter is not None and str(status_filter.value or "").strip():
                        any_chip = True
                        label = str(status_filter.options.get(status_filter.value) or status_filter.value)

                        def _clear_status() -> None:
                            status_filter.value = ""
                            status_filter.update()
                            _refresh_list()

                        _chip(f"Status: {label}", _clear_status)

                    if str(sort_filter.value or "").strip():
                        any_chip = True
                        sort_label = str(sort_filter.options.get(sort_filter.value) or sort_filter.value)

                        def _clear_sort() -> None:
                            sort_filter.value = ""
                            sort_filter.update()
                            _refresh_list()

                        _chip(f"Sort: {sort_label}", _clear_sort)

                if not any_chip:
                    return

            @ui.refreshable
            def paths_list() -> None:
                nonlocal visible_count
                needle = str(q.value or "").strip().lower()
                status_v = str(status_filter.value or "").strip()
                sort_v = str(sort_filter.value or "").strip()
                scope_v = str(scope_filter.value or "all")
                shown = _filter_paths(paths, needle)

                if scope_v == "selected":
                    shown = [p for p in shown if int(p.get("id") or 0) in selected_by_id]

                if status_v:
                    shown = [p for p in shown if _path_matches_state(int(p.get("id") or 0), selected_by_id, status_v)]

                if sort_v:
                    if sort_v == "name_az":
                        shown = sorted(shown, key=lambda p: str(p.get("name") or "").strip().lower())
                    elif sort_v == "newest":

                        def _created_key(p: dict[str, Any]) -> tuple[datetime, int]:
                            dt = _parse_iso_datetime(p.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)
                            return (dt, int(p.get("id") or 0))

                        shown = sorted(shown, key=_created_key, reverse=True)
                    elif sort_v == "top_rated":

                        def _top_rated_key(p: dict[str, Any]) -> tuple[float, int, int]:
                            pid = int(p.get("id") or 0)
                            row = path_review_summary_by_id.get(pid) or {}
                            try:
                                avg = float(row.get("avg_rating") or 0.0)
                            except (TypeError, ValueError):
                                avg = 0.0
                            try:
                                count = int(row.get("review_count") or 0)
                            except (TypeError, ValueError):
                                count = 0
                            return (avg, count, pid)

                        shown = sorted(shown, key=_top_rated_key, reverse=True)
                    elif sort_v == "most_reviewed":

                        def _most_reviewed_key(p: dict[str, Any]) -> tuple[int, float, int]:
                            pid = int(p.get("id") or 0)
                            row = path_review_summary_by_id.get(pid) or {}
                            try:
                                count = int(row.get("review_count") or 0)
                            except (TypeError, ValueError):
                                count = 0
                            try:
                                avg = float(row.get("avg_rating") or 0.0)
                            except (TypeError, ValueError):
                                avg = 0.0
                            return (count, avg, pid)

                        shown = sorted(shown, key=_most_reviewed_key, reverse=True)

                with ui.column().classes("w-full gap-3"):
                    if loading or not loaded_once:
                        render_card_skeletons(count=4)
                        return

                    if not shown:
                        any_filters = any([str(q.value or "").strip(), str(status_filter.value or "").strip()])
                        if scope_v == "selected" and not any_filters:
                            ui.label("No selected paths yet.").classes("text-sm").style("color: var(--lp-muted)")
                            ui.label("Browse paths and select one to start tracking.").classes("text-sm").style(
                                "color: var(--lp-muted)"
                            )
                            with ui.row().classes("items-center gap-2"):
                                ui.button(
                                    "Browse all paths",
                                    on_click=lambda: setattr(scope_filter, "value", "all") or _refresh_list(),
                                ).props("outline")
                                ui.button("Refresh", on_click=_load_all).props("outline")
                            return
                        if not paths and not any_filters:
                            ui.label("No paths yet.").classes("text-sm").style("color: var(--lp-muted)")
                            ui.label("Share the first path to get started.").classes("text-sm").style("color: var(--lp-muted)")
                            with ui.row().classes("items-center gap-2"):
                                ui.button("Share a path", on_click=_open_create_dialog).props("outline")
                                ui.button("Browse courses", on_click=lambda: ui.navigate.to("/courses")).props("outline")
                            return
                        ui.label("No paths match your filters.").classes("text-sm").style("color: var(--lp-muted)")
                        with ui.row().classes("items-center gap-2"):
                            ui.button("Reset all", on_click=_reset_all).props("outline")
                            ui.button("Refresh", on_click=_load_all).props("outline")
                        return

                    total = len(shown)
                    shown_page = shown[: max(0, int(visible_count))]
                    for p in shown_page:
                        pid = int(p.get("id") or 0)
                        selected = selected_by_id.get(pid)
                        can_edit = is_admin or (str(p.get("created_by") or "") == username)
                        is_tracked = selected is not None
                        st_cls = " lp-accent-card--interested" if is_tracked else ""
                        detail = selected_detail_by_path_id.get(pid) if selected else None
                        completed, total_courses, progress = (0, 0, 0.0)
                        if isinstance(detail, dict):
                            completed, total_courses, progress = compute_path_progress(
                                detail=detail, tracking_by_course_id=tracking_by_course_id
                            )

                        created_at = _parse_iso_datetime(p.get("created_at"))
                        updated_at = _parse_iso_datetime(p.get("updated_at"))
                        is_updated = (
                            _is_recent(updated_at)
                            and created_at is not None
                            and updated_at is not None
                            and updated_at > created_at
                        )
                        is_new = (not is_updated) and _is_recent(created_at)

                        with ui.card().classes(f"w-full lp-accent-card lp-card--hover{st_cls}"):
                            with ui.element("div").classes("lp-card-topright"):
                                if is_new:
                                    ui.label("New").classes("lp-chip lp-chip--sky")
                                elif is_updated:
                                    ui.label("Updated").classes("lp-chip lp-chip--teal")
                                if can_edit:

                                    async def _do_edit(_pid: int = pid) -> None:
                                        detail = await api.get(f"/paths/{_pid}")
                                        await _open_edit(path_id=_pid, detail=detail, detail_dialog=None)

                                    async def _do_delete(_pid: int = pid) -> None:
                                        await _delete_path(_pid)

                                    render_owner_menu(
                                        on_edit=_do_edit,
                                        on_delete=_do_delete,
                                    )

                            ui.label(p.get("name") or "").classes("text-lg font-semibold")
                            if str(p.get("description") or "").strip():
                                ui.label(p.get("description") or "").classes("text-sm text-gray-600")
                            with ui.row().classes("items-center gap-2 flex-wrap mt-1"):
                                shared_by = str(p.get("created_by") or "").strip()
                                if shared_by:
                                    ui.label(f"Shared by {shared_by}").classes("text-xs").style("color: var(--lp-muted)")
                                rating_badge = _format_rating_badge(path_review_summary_by_id.get(pid))
                                if rating_badge:
                                    ui.label(rating_badge).classes("lp-chip lp-chip--subtle")
                                ui.label(_path_tracking_label(is_tracked)).classes(_path_tracking_chip_class(is_tracked))
                            if selected and total_courses:
                                ui.label(f"{completed}/{total_courses} completed").classes("text-sm").style(
                                    "color: var(--lp-muted)"
                                )
                                ui.linear_progress(progress, show_value=False).classes("w-full")

                            with ui.row().classes("items-center gap-2 mt-2"):

                                async def _view(_pid: int = pid) -> None:
                                    await _open_details(_pid, view_mode="full")

                                async def _review(_pid: int = pid) -> None:
                                    await _open_details(_pid, view_mode="reviews")

                                render_view_review_actions(
                                    on_view=_view,
                                    on_review=_review,
                                )

                                if selected:

                                    async def _do_unselect(_pid: int = pid) -> None:
                                        await _unselect(_pid)
                                        _recompute_facet_options()

                                    ui.button("Untrack", on_click=_do_unselect).props("outline dense")
                                else:

                                    async def _do_select(_pid: int = pid) -> None:
                                        await _select(_pid)
                                        _recompute_facet_options()

                                    ui.button("Track", on_click=_do_select).props("outline dense")

                    if total > len(shown_page):
                        with ui.row().classes("items-center justify-center mt-2"):

                            def _load_more() -> None:
                                nonlocal visible_count
                                visible_count = min(total, int(visible_count) + page_size)
                                paths_list.refresh()

                            ui.button(f"Load more ({len(shown_page)}/{total})", on_click=_load_more).props("outline")

            async def _load_all() -> None:
                """Reload all data for this page."""
                nonlocal paths
                nonlocal selected_by_id
                nonlocal selected_detail_by_path_id
                nonlocal tracking_by_course_id
                nonlocal courses
                nonlocal course_by_id
                nonlocal path_review_summary_by_id
                nonlocal loading
                nonlocal loaded_once
                nonlocal visible_count
                if loading:
                    return
                loading = True
                visible_count = page_size
                refresh_btn.disable()
                meta.text = "Loading..."
                paths_list.refresh()
                try:
                    paths, selected_by_id, courses, course_by_id = await _load_paths_page_data(api)
                    await asyncio.gather(_reload_tracking(), _reload_selected_details())
                    path_ids: list[int] = []
                    for p in paths:
                        if not isinstance(p, dict):
                            continue
                        try:
                            pid = int(p.get("id") or 0)
                        except (TypeError, ValueError):
                            continue
                        if pid > 0:
                            path_ids.append(pid)
                    path_review_summary_by_id = {}
                    if path_ids:
                        try:
                            summaries = await api.get("/paths/reviews/summary", params={"path_ids": path_ids})
                            for row in list(summaries or []):
                                if not isinstance(row, dict):
                                    continue
                                try:
                                    pid = int(row.get("path_id") or 0)
                                except (TypeError, ValueError):
                                    continue
                                if pid > 0:
                                    path_review_summary_by_id[pid] = row
                        except ApiError:
                            path_review_summary_by_id = {}
                    create_course_ids.options = _course_options(courses)
                    create_course_ids.update()
                    _recompute_facet_options()
                    paths_list.refresh()
                    meta.text = f"{len(paths)} paths"
                except ApiError as exc:
                    ui.notify(str(exc), type="negative")
                    paths = []
                    selected_by_id = {}
                    courses = []
                    course_by_id = {}
                    path_review_summary_by_id = {}
                    _recompute_facet_options()
                    paths_list.refresh()
                    meta.text = "Failed to load"
                finally:
                    loading = False
                    loaded_once = True
                    refresh_btn.enable()
                    paths_list.refresh()

            def _render_rail() -> None:
                nonlocal status_filter, refresh_btn
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label("Filters").classes("text-md font-semibold")
                    refresh_btn = ui.button("Refresh", on_click=_load_all).props("outline dense")

                ui.label("Tip: select a path to track progress.").classes("text-xs").style("color: var(--lp-muted)")

                status_filter = ui.select({"": "Any state"}, label="Path state", value="").props("dense").classes("w-full")
                status_filter.on("update:model-value", _refresh_list)

                ui.element("div").style("flex: 1")
                ui.button("Clear", on_click=_reset_all).props("outline dense").classes("w-full")

            def _render_main() -> None:
                active_filters()
                paths_list()

            render_split_layout(rail=_render_rail, main=_render_main, rail_classes="lp-rail--bar")

            await _load_all()
