"""Paths browse/admin page for the NiceGUI frontend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from nicegui import app, ui

from frontend.ui.nicegui.components.layout import render_container, render_shell, render_split_layout
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.path_card import render_path_card
from frontend.ui.nicegui.components.path_detail_sections import (
    render_path_detail_header,
    render_path_detail_learning_section,
)
from frontend.ui.nicegui.components.paths_sections import render_paths_filter_rail, render_paths_topbar
from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.datetime_utils import is_recent, parse_iso_datetime
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.navigation_intents import get_path_intent, pop_path_intent
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.paths.controller import PathsPageController
from frontend.ui.nicegui.pages.paths.state import PathsPageState
from frontend.ui.nicegui.services.paths_service import (
    compute_path_progress,
)


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


def _format_recommendation_badge(row: dict[str, Any] | None) -> str:
    """Format a compact recommendation badge for path cards."""
    if not isinstance(row, dict):
        return ""
    try:
        count = int(row.get("recommendation_count") or 0)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return ""
    return f"↗ {count} rec"


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


def _path_outcomes(
    *,
    detail: dict[str, Any],
    tracking_by_course_id: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    """Compute path milestone + next-step metadata for UX rendering."""
    completed, total, ratio = compute_path_progress(detail=detail, tracking_by_course_id=tracking_by_course_id)
    courses = [c for c in list(detail.get("courses") or []) if isinstance(c, dict)]
    next_course: dict[str, Any] | None = None
    in_progress = 0
    for c in courses:
        try:
            cid = int(c.get("id") or 0)
        except (TypeError, ValueError):
            continue
        status = str((tracking_by_course_id.get(cid) or {}).get("status") or "").strip()
        if status == "in_progress":
            in_progress += 1
        if next_course is None and status != "completed":
            next_course = c

    remaining = max(0, int(total) - int(completed))
    if total <= 0:
        milestone = "No courses"
        milestone_class = "lp-chip lp-chip--muted"
        impact = "Add courses to define this path."
    elif remaining == 0:
        milestone = "Completed"
        milestone_class = "lp-chip lp-chip--lime"
        impact = "All courses completed."
    elif completed <= 0:
        milestone = "Not started"
        milestone_class = "lp-chip lp-chip--muted"
        impact = f"{remaining} course(s) left to complete this path."
    elif ratio >= 0.5:
        milestone = "Halfway"
        milestone_class = "lp-chip lp-chip--teal"
        impact = f"{remaining} course(s) left to complete this path."
    else:
        milestone = "Started"
        milestone_class = "lp-chip lp-chip--sky"
        impact = f"{remaining} course(s) left to complete this path."

    if in_progress > 0 and remaining > 0:
        impact = f"{impact} {in_progress} in progress."

    return {
        "completed": completed,
        "total": total,
        "ratio": ratio,
        "next_course": next_course,
        "milestone": milestone,
        "milestone_class": milestone_class,
        "impact": impact,
    }


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
        controller = PathsPageController(api=api)
        controller_state = PathsPageState()

        loading = False
        loaded_once = False
        page_size = 10
        visible_count = page_size

        async def _reload_selected() -> None:
            """Reload selected path rows (used after select/unselect/status updates)."""
            try:
                await controller.reload_selected(state=controller_state)
            except ApiError as exc:
                ui.notify(str(exc), type="negative")
                controller_state.selected_by_id = {}
                return

        async def _reload_tracking() -> None:
            """Reload the current user's tracking map (used to compute path progress)."""
            try:
                await controller.reload_tracking(state=controller_state)
            except ApiError:
                controller_state.tracking_by_course_id = {}
                return

        async def _reload_selected_details() -> None:
            """Reload path detail payloads for currently selected paths."""
            await controller.reload_selected_details(state=controller_state)

        async def _ensure_selected_detail(path_id: int) -> None:
            """Ensure a selected path has a detail payload cached."""
            try:
                await controller.ensure_selected_detail(path_id=int(path_id), state=controller_state)
            except ApiError:
                return

        @guard_ui_action(title="Select failed")
        async def _select(path_id: int) -> None:
            seeded, detail = await controller.select_path(path_id=int(path_id), state=controller_state)
            await _reload_selected()
            if isinstance(detail, dict):
                controller_state.selected_detail_by_path_id[int(path_id)] = detail
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
            await controller.unselect_path(path_id=int(path_id))
            await _reload_selected()
            controller_state.selected_detail_by_path_id.pop(int(path_id), None)
            paths_list.refresh()

        @guard_ui_action(title="Delete path failed")
        async def _delete_path(path_id: int) -> None:
            await controller.delete_path(path_id=int(path_id))
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
                    {cid: f"{c.get('title') or ''} (#{cid})" for cid, c in sorted(controller_state.course_by_id.items())},
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
                            c = controller_state.course_by_id.get(cid) or {}
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
                        await controller.update_path(path_id=int(path_id), payload=payload)
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
            bundle = await controller.load_path_detail_bundle(path_id=int(path_id))
            detail = dict(bundle.detail or {})
            normalized_view_mode = _normalize_path_view_mode(view_mode)
            path_reviews: list[dict[str, Any]] = list(bundle.path_reviews or [])
            path_recommendations: list[dict[str, Any]] = list(bundle.path_recommendations or [])

            courses_rows = list((detail.get("courses") or []) if isinstance(detail, dict) else [])
            outcomes = _path_outcomes(
                detail=detail if isinstance(detail, dict) else {},
                tracking_by_course_id=controller_state.tracking_by_course_id,
            )
            completed = int(outcomes.get("completed") or 0)
            total_courses = int(outcomes.get("total") or 0)
            progress = float(outcomes.get("ratio") or 0.0)

            review_summary_by_course_id: dict[int, dict[str, Any]] = dict(bundle.course_review_summary_by_course_id or {})

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
                return str((controller_state.tracking_by_course_id.get(int(cid)) or {}).get("status") or "").strip()

            courses_rows = [
                dict(
                    c,
                    reviews=_summary_label(int(c.get("id") or 0)),
                    tracking_status=_course_tracking_status(int(c.get("id") or 0)),
                )
                for c in courses_rows
                if isinstance(c, dict)
            ]

            next_course: dict[str, Any] | None = outcomes.get("next_course") if isinstance(outcomes, dict) else None

            with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(900px,95vw)]"):
                summary = _format_review_summary(controller_state.path_review_summary_by_id.get(int(path_id)))
                rec_badge = _format_recommendation_badge(controller_state.path_recommendation_summary_by_id.get(int(path_id)))
                rec_by = sorted(
                    {
                        str(r.get("created_by") or "").strip()
                        for r in path_recommendations
                        if isinstance(r, dict) and str(r.get("created_by") or "").strip()
                    }
                )
                timestamps: list[str] = []
                for row in list(path_reviews) + list(path_recommendations):
                    if not isinstance(row, dict):
                        continue
                    created_at = str(row.get("created_at") or "").strip()
                    if created_at:
                        timestamps.append(created_at)
                latest_activity = max(timestamps)[:10] if timestamps else ""
                render_path_detail_header(
                    name=str(detail.get("name") or ""),
                    description=str(detail.get("description") or ""),
                    review_summary=summary,
                    recommendation_badge=rec_badge,
                    recommended_by=", ".join(rec_by[:3]),
                    latest_activity=latest_activity,
                )
                if normalized_view_mode != "reviews":
                    is_tracked = int(path_id) in controller_state.selected_by_id

                    @guard_ui_action(title="Open next course failed")
                    async def _open_next() -> None:
                        if next_course is None:
                            return
                        url = str(next_course.get("url") or "").strip()
                        if url:
                            ui.navigate.to(url, new_tab=True)
                            return
                        ui.notify("Next course has no URL yet", type="warning")

                    render_path_detail_learning_section(
                        total_courses=total_courses,
                        completed=completed,
                        progress=progress,
                        milestone=str(outcomes.get("milestone") or ""),
                        milestone_class=str(outcomes.get("milestone_class") or ""),
                        impact=str(outcomes.get("impact") or ""),
                        is_tracked=is_tracked,
                        tracking_label_text=_path_tracking_label(is_tracked),
                        next_title=str(next_course.get("title") or "").strip() if isinstance(next_course, dict) else "",
                        on_open_next=_open_next if isinstance(next_course, dict) else None,
                        courses_rows=courses_rows,
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
                        controller_state.path_review_summary_by_id[int(path_id)] = {
                            "path_id": int(path_id),
                            "avg_rating": 0.0,
                            "review_count": 0,
                        }
                    else:
                        avg = float(sum(ratings)) / float(len(ratings))
                        controller_state.path_review_summary_by_id[int(path_id)] = {
                            "path_id": int(path_id),
                            "avg_rating": float(avg),
                            "review_count": int(len(ratings)),
                        }
                    paths_list.refresh()

                async def _save_path_review(rating: int, text: str) -> dict[str, Any]:
                    return await controller.save_path_review(path_id=int(path_id), rating=int(rating), text=str(text or ""))

                async def _delete_path_review(review_id: int) -> bool:
                    return await controller.delete_path_review(path_id=int(path_id), review_id=int(review_id))

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
                ui.label("Save a draft if you want feedback before publishing.").classes("text-xs").style(
                    "color: var(--lp-muted)"
                )
                create_name = ui.input("Name").props("clearable").classes("w-full")
                create_description = ui.textarea("Description").props("autogrow").classes("w-full")
                create_course_ids = ui.select({}, label="Courses (ordered)", multiple=True).classes("w-full")

                path_draft_key = f"paths_share_draft::{username}"

                def _path_draft_payload() -> dict[str, Any]:
                    return {
                        "name": str(create_name.value or ""),
                        "description": str(create_description.value or ""),
                        "course_ids": list(create_course_ids.value or []),
                    }

                def _apply_path_draft(raw: Any) -> None:
                    draft = raw if isinstance(raw, dict) else {}
                    create_name.value = str(draft.get("name") or "")
                    create_description.value = str(draft.get("description") or "")
                    create_course_ids.value = list(draft.get("course_ids") or [])
                    create_course_ids.update()

                with ui.row().classes("justify-end mt-4"):

                    def _save_draft() -> None:
                        app.storage.user[path_draft_key] = _path_draft_payload()
                        ui.notify("Draft saved", type="positive")

                    def _load_draft() -> None:
                        draft = app.storage.user.get(path_draft_key)
                        if not isinstance(draft, dict):
                            ui.notify("No saved draft found", type="warning")
                            return
                        _apply_path_draft(draft)
                        ui.notify("Draft loaded", type="positive")

                    @guard_ui_action(title="Share path failed")
                    async def _create_submit() -> None:
                        payload = {
                            "name": str(create_name.value or ""),
                            "description": str(create_description.value or ""),
                            "course_ids": list(create_course_ids.value or []),
                        }
                        await controller.create_path(payload=payload)
                        app.storage.user.pop(path_draft_key, None)
                        ui.notify("Path shared", type="positive")
                        create_dialog.close()
                        await _load_all()

                    ui.button("Save draft", on_click=_save_draft).props("outline")
                    ui.button("Load draft", on_click=_load_draft).props("outline")
                    ui.button("Share", on_click=_create_submit)
                    ui.button("Cancel", on_click=create_dialog.close).props("outline")

            def _open_create_dialog() -> None:
                _apply_path_draft(app.storage.user.get(path_draft_key))
                create_dialog.open()

            # Top bar (search + primary action + sort + count).
            request = getattr(ui.context.client, "request", None)
            query_params = getattr(request, "query_params", {}) if request is not None else {}
            initial_tab = str(getattr(query_params, "get", lambda _k, _d=None: _d)("tab", "") or "").strip().lower()
            initial_scope = "selected" if initial_tab == "selected" else "all"
            initial_path_id_raw = str(getattr(query_params, "get", lambda _k, _d=None: _d)("path_id", "") or "").strip()
            try:
                initial_path_id = int(initial_path_id_raw) if initial_path_id_raw else 0
            except (TypeError, ValueError):
                initial_path_id = 0
            initial_view_mode = str(getattr(query_params, "get", lambda _k, _d=None: _d)("view", "") or "").strip().lower()
            initial_dialog_mode = _normalize_path_view_mode(initial_view_mode)
            intent = app.storage.user.get("paths_open_intent")
            nav_intent = get_path_intent(username=username)
            if isinstance(intent, dict):
                if initial_path_id <= 0:
                    try:
                        initial_path_id = int(intent.get("path_id") or 0)
                    except (TypeError, ValueError):
                        initial_path_id = 0
                if initial_view_mode not in {"full", "reviews"}:
                    initial_dialog_mode = _normalize_path_view_mode(intent.get("view"))
            if isinstance(nav_intent, dict):
                if initial_path_id <= 0:
                    try:
                        initial_path_id = int(nav_intent.get("path_id") or 0)
                    except (TypeError, ValueError):
                        initial_path_id = 0
                if initial_view_mode not in {"full", "reviews"}:
                    initial_dialog_mode = _normalize_path_view_mode(nav_intent.get("view"))

            q, scope_filter, sort_filter, meta = render_paths_topbar(
                initial_scope=initial_scope,
                on_open_create_dialog=_open_create_dialog,
            )

            def _status_key(pid: int) -> str:
                return "tracked" if int(pid) in controller_state.selected_by_id else "not_tracked"

            def _recompute_facet_options() -> None:
                """Recompute status facet options with counts based on the current local filters."""
                if status_filter is None:
                    return
                scope_v = str(scope_filter.value or "all")
                needle = str(q.value or "").strip().lower()

                def _passes(p: dict[str, Any], *, ignore: str) -> bool:
                    if ignore != "scope" and scope_v == "selected":
                        pid = int(p.get("id") or 0)
                        if pid <= 0 or pid not in controller_state.selected_by_id:
                            return False
                    if needle and ignore != "needle":
                        if (
                            needle not in str(p.get("name") or "").lower()
                            and needle not in str(p.get("description") or "").lower()
                        ):
                            return False
                    if ignore != "status":
                        status_v = str(status_filter.value or "").strip()
                        if status_v and not _path_matches_state(
                            int(p.get("id") or 0), controller_state.selected_by_id, status_v
                        ):
                            return False
                    return True

                counts: dict[str, int] = {"not_tracked": 0, "tracked": 0}
                for p in controller_state.paths:
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
                shown = _filter_paths(controller_state.paths, needle)

                if scope_v == "selected":
                    shown = [p for p in shown if int(p.get("id") or 0) in controller_state.selected_by_id]

                if status_v:
                    shown = [
                        p
                        for p in shown
                        if _path_matches_state(int(p.get("id") or 0), controller_state.selected_by_id, status_v)
                    ]

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
                            row = controller_state.path_review_summary_by_id.get(pid) or {}
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
                            row = controller_state.path_review_summary_by_id.get(pid) or {}
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
                        if not controller_state.paths and not any_filters:
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
                        selected = controller_state.selected_by_id.get(pid)
                        can_edit = is_admin or (str(p.get("created_by") or "") == username)
                        is_tracked = selected is not None
                        st_cls = " lp-accent-card--interested" if is_tracked else ""
                        detail = controller_state.selected_detail_by_path_id.get(pid) if selected else None
                        completed, total_courses, progress = (0, 0, 0.0)
                        outcomes: dict[str, Any] = {}
                        if isinstance(detail, dict):
                            outcomes = _path_outcomes(
                                detail=detail,
                                tracking_by_course_id=controller_state.tracking_by_course_id,
                            )
                            completed = int(outcomes.get("completed") or 0)
                            total_courses = int(outcomes.get("total") or 0)
                            progress = float(outcomes.get("ratio") or 0.0)

                        created_at = _parse_iso_datetime(p.get("created_at"))
                        updated_at = _parse_iso_datetime(p.get("updated_at"))
                        is_updated = (
                            _is_recent(updated_at)
                            and created_at is not None
                            and updated_at is not None
                            and updated_at > created_at
                        )
                        is_new = (not is_updated) and _is_recent(created_at)
                        rating_badge = _format_rating_badge(controller_state.path_review_summary_by_id.get(pid))
                        recommendation_badge = _format_recommendation_badge(
                            controller_state.path_recommendation_summary_by_id.get(pid)
                        )
                        shared_by = str(p.get("created_by") or "").strip()
                        milestone = str(outcomes.get("milestone") or "") if selected else ""
                        milestone_class = str(outcomes.get("milestone_class") or "") if selected else ""
                        impact = str(outcomes.get("impact") or "") if selected else ""
                        next_course = outcomes.get("next_course") if isinstance(outcomes, dict) else None
                        next_title = str(next_course.get("title") or "").strip() if isinstance(next_course, dict) else ""

                        @guard_ui_action(title="Recommend failed")
                        async def _recommend(_pid: int = pid) -> None:
                            existing_note = ""
                            try:
                                existing_note = await controller.get_user_recommendation_note(
                                    path_id=int(_pid), username=username
                                )
                            except ApiError:
                                existing_note = ""

                            with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(600px,95vw)]"):
                                ui.label("Recommend path").classes("text-lg font-semibold")
                                note = (
                                    ui.textarea("Why this helps (optional)", value=existing_note)
                                    .props("autogrow")
                                    .classes("w-full")
                                )
                                with ui.row().classes("justify-end mt-4"):

                                    @guard_ui_action(title="Recommend failed")
                                    async def _save() -> None:
                                        await controller.save_recommendation(
                                            path_id=int(_pid),
                                            note=str(note.value or ""),
                                        )
                                        ui.notify("Recommendation saved", type="positive")
                                        dialog.close()
                                        await _load_all()

                                    ui.button("Save", on_click=_save)
                                    ui.button("Cancel", on_click=dialog.close).props("outline")

                            dialog.open()

                        def _copy_path_link(_pid: int = pid) -> None:
                            link = f"/paths?path_id={int(_pid)}&view=full"
                            ui.run_javascript(f"navigator.clipboard.writeText(window.location.origin + {repr(link)});")
                            ui.notify("Link copied", type="positive")

                        async def _do_review(_pid: int = pid) -> None:
                            await _open_details(_pid, view_mode="reviews")

                        async def _do_edit(_pid: int = pid) -> None:
                            detail = await controller.get_path_detail(path_id=int(_pid))
                            await _open_edit(path_id=_pid, detail=detail, detail_dialog=None)

                        async def _do_delete(_pid: int = pid) -> None:
                            await _delete_path(_pid)

                        async def _view(_pid: int = pid) -> None:
                            await _open_details(_pid, view_mode="full")

                        if selected:

                            async def _do_unselect(_pid: int = pid) -> None:
                                await _unselect(_pid)
                                _recompute_facet_options()

                            on_track_toggle = _do_unselect
                            track_toggle_label = "Untrack"
                        else:

                            async def _do_select(_pid: int = pid) -> None:
                                await _select(_pid)
                                _recompute_facet_options()

                            on_track_toggle = _do_select
                            track_toggle_label = "Track"

                        render_path_card(
                            path_row=p,
                            card_class_suffix=st_cls,
                            is_new=is_new,
                            is_updated=is_updated,
                            rating_badge=rating_badge,
                            recommendation_badge=recommendation_badge,
                            can_edit=can_edit,
                            shared_by=shared_by,
                            tracking_label_text=_path_tracking_label(is_tracked),
                            tracking_chip_cls=_path_tracking_chip_class(is_tracked),
                            completed=int(completed if selected else 0),
                            total_courses=int(total_courses if selected else 0),
                            progress=float(progress if selected else 0.0),
                            milestone=milestone,
                            milestone_class=milestone_class,
                            impact=impact,
                            next_title=next_title,
                            on_review=_do_review,
                            on_recommend=_recommend,
                            on_copy_link=_copy_path_link,
                            on_edit=_do_edit,
                            on_delete=_do_delete,
                            on_view=_view,
                            on_track_toggle=on_track_toggle,
                            track_toggle_label=track_toggle_label,
                        )

                    if total > len(shown_page):
                        with ui.row().classes("items-center justify-center mt-2"):

                            def _load_more() -> None:
                                nonlocal visible_count
                                visible_count = min(total, int(visible_count) + page_size)
                                paths_list.refresh()

                            ui.button(f"Load more ({len(shown_page)}/{total})", on_click=_load_more).props("outline")

            async def _load_all() -> None:
                """Reload all data for this page."""
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
                    await controller.load_all(state=controller_state)
                    create_course_ids.options = _course_options(controller_state.courses)
                    create_course_ids.update()
                    _recompute_facet_options()
                    paths_list.refresh()
                    meta.text = f"{len(controller_state.paths)} paths"
                except ApiError as exc:
                    ui.notify(str(exc), type="negative")
                    controller_state.paths = []
                    controller_state.selected_by_id = {}
                    controller_state.selected_detail_by_path_id = {}
                    controller_state.tracking_by_course_id = {}
                    controller_state.courses = []
                    controller_state.course_by_id = {}
                    controller_state.path_review_summary_by_id = {}
                    controller_state.path_recommendation_summary_by_id = {}
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
                status_filter, refresh_btn = render_paths_filter_rail(
                    on_refresh=_load_all,
                    on_reset=_reset_all,
                    on_status_change=_refresh_list,
                )

            def _render_main() -> None:
                active_filters()
                paths_list()

            render_split_layout(rail=_render_rail, main=_render_main, rail_classes="lp-rail--bar")

            await _load_all()
            if initial_path_id > 0:
                await _open_details(initial_path_id, view_mode=initial_dialog_mode)
                if isinstance(intent, dict):
                    try:
                        if int(intent.get("path_id") or 0) == int(initial_path_id):
                            app.storage.user.pop("paths_open_intent", None)
                    except (TypeError, ValueError):
                        pass
                if isinstance(nav_intent, dict):
                    try:
                        if int(nav_intent.get("path_id") or 0) == int(initial_path_id):
                            pop_path_intent(username=username)
                    except (TypeError, ValueError):
                        pass
