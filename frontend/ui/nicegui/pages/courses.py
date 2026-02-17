"""Courses browse/admin page for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from typing import Any

from nicegui import app, ui

from frontend.ui.nicegui.components.layout import render_container, render_shell, render_split_layout
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.reviews_panel import render_reviews_panel
from frontend.ui.nicegui.components.status_chips import tracking_chip_class, tracking_label, TRACKING_STATUS_OPTIONS
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.datetime_utils import is_recent, parse_iso_datetime
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.navigation_intents import get_course_intent, pop_course_intent
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.services.courses_service import (
    load_courses_and_tracking,
    load_recommendation_summaries,
    load_review_summaries,
    load_tracking_map,
)


def _parse_duration_hours(raw: str) -> float | None:
    s = raw.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _format_review_summary(row: dict[str, Any] | None) -> str:
    """Format a course review summary row into a compact label."""
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
    """Format a compact rating badge for course cards (e.g., "★ 4.2 (12)")."""
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
    return f"★ {avg:.1f} ({count})"


def _format_recommendation_badge(row: dict[str, Any] | None) -> str:
    """Format a compact recommendation badge for course cards."""
    if not isinstance(row, dict):
        return ""
    try:
        count = int(row.get("recommendation_count") or 0)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return ""
    return f"↗ {count} rec"


def _status_for_card(tracked: dict[str, Any] | None) -> str:
    """Return a stable tracking status string for card styling."""
    v = str((tracked or {}).get("status") or "").strip()
    if v in {"interested", "in_progress", "completed"}:
        return v
    return ""


_parse_iso_datetime = parse_iso_datetime
_is_recent = is_recent


def _format_short_date(value: Any) -> str:
    """Format an ISO datetime into a compact human-readable date (e.g., 'Feb 13, 2026')."""
    dt = _parse_iso_datetime(value)
    if dt is None:
        return str(value or "").strip()
    return dt.astimezone(timezone.utc).strftime("%b %d, %Y")


def _normalize_course_view_mode(focus_reviews: bool) -> str:
    """Map bool focus flag to stable view mode string."""
    return "reviews" if bool(focus_reviews) else "full"


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register the `/courses` route.

    Args:
        store: Session store.
        api: API client.
    """

    @ui.page("/courses")
    async def courses_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return
        render_shell(title="Courses", store=store, api=api)
        username = str(user.get("username") or "")
        is_admin = str(user.get("role") or "") == "admin"

        with render_container():
            courses: list[dict[str, Any]] = []
            tracking_by_course_id: dict[int, dict[str, Any]] = {}
            review_summary_by_course_id: dict[int, dict[str, Any]] = {}
            recommendation_summary_by_course_id: dict[int, dict[str, Any]] = {}
            page_size = 10
            visible_count = page_size

            request = getattr(ui.context.client, "request", None)
            query_params = getattr(request, "query_params", {}) if request is not None else {}
            initial_tab = str(getattr(query_params, "get", lambda _k, _d=None: _d)("tab", "") or "").strip().lower()
            initial_scope = "tracked" if initial_tab == "tracked" else "all"
            initial_course_id_raw = str(getattr(query_params, "get", lambda _k, _d=None: _d)("course_id", "") or "").strip()
            try:
                initial_course_id = int(initial_course_id_raw) if initial_course_id_raw else 0
            except (TypeError, ValueError):
                initial_course_id = 0
            initial_view_mode = str(getattr(query_params, "get", lambda _k, _d=None: _d)("view", "") or "").strip().lower()
            initial_focus_reviews = initial_view_mode == "reviews"
            intent = app.storage.user.get("courses_open_intent")
            nav_intent = get_course_intent(username=username)
            if isinstance(intent, dict):
                if initial_course_id <= 0:
                    try:
                        initial_course_id = int(intent.get("course_id") or 0)
                    except (TypeError, ValueError):
                        initial_course_id = 0
                if initial_view_mode not in {"full", "reviews"}:
                    initial_focus_reviews = str(intent.get("view") or "").strip().lower() == "reviews"
            if isinstance(nav_intent, dict):
                if initial_course_id <= 0:
                    try:
                        initial_course_id = int(nav_intent.get("course_id") or 0)
                    except (TypeError, ValueError):
                        initial_course_id = 0
                if initial_view_mode not in {"full", "reviews"}:
                    initial_focus_reviews = str(nav_intent.get("view") or "").strip().lower() == "reviews"

            with ui.row().classes("lp-topbar"):
                q = ui.input("Search courses").props("clearable debounce=300").style("flex: 1")
                with ui.row().classes("items-center gap-2").style("margin-left: auto"):
                    ui.button("Share", on_click=lambda: _open_create_dialog()).props("dense")
                    scope_filter = (
                        ui.radio(
                            {"all": "All", "tracked": "Tracked"},
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
                                "title_az": "Title A–Z",
                            },
                            value="",
                            label=None,
                        )
                        .props("dense")
                        .style("min-width: 180px")
                    )
                    # Late-bind to avoid "defined later" ordering issues.
                    sort_filter.on("update:model-value", lambda *_: _refresh_list())
                    scope_filter.on("update:model-value", lambda *_: _refresh_list())
                    meta = ui.label("").classes("lp-topbar-meta")

            loading = False
            loaded_once = False

            provider_filter: Any = None
            category_filter: Any = None
            level_filter: Any = None
            status_filter: Any = None
            refresh_btn: Any = None

            def _recompute_facet_options() -> None:
                """Recompute facet dropdown options with counts based on the current local filters.

                Counts are computed "excluding the facet itself" (standard faceting), so users can see
                the impact of picking a different value before clicking it.
                """

                needle = str(q.value or "").strip().lower()
                scope_v = str(scope_filter.value or "all")

                def _matches_needle(course: dict[str, Any]) -> bool:
                    if not needle:
                        return True
                    return (
                        needle in str(course.get("title") or "").lower()
                        or needle in str(course.get("description") or "").lower()
                    )

                def _status_key(course_id: int) -> str:
                    tracked = tracking_by_course_id.get(int(course_id))
                    v = str((tracked or {}).get("status") or "").strip()
                    if v in {"interested", "in_progress", "completed"}:
                        return v
                    return "not_tracked"

                def _passes(course: dict[str, Any], *, ignore: str) -> bool:
                    if ignore != "scope" and scope_v == "tracked":
                        cid = int(course.get("id") or 0)
                        if cid <= 0 or cid not in tracking_by_course_id:
                            return False
                    if ignore != "needle" and not _matches_needle(course):
                        return False

                    if ignore != "provider":
                        provider_v = str(provider_filter.value or "").strip().lower()
                        if provider_v and provider_v != str(course.get("provider") or "").strip().lower():
                            return False

                    if ignore != "category":
                        category_v = str(category_filter.value or "").strip().lower()
                        if category_v and category_v != str(course.get("category") or "").strip().lower():
                            return False

                    if ignore != "level":
                        level_v = str(level_filter.value or "").strip().lower()
                        if level_v and level_v != str(course.get("level") or "").strip().lower():
                            return False

                    if ignore != "status":
                        status_v = str(status_filter.value or "").strip()
                        if status_v:
                            cid = int(course.get("id") or 0)
                            if status_v == "not_tracked":
                                if cid in tracking_by_course_id:
                                    return False
                            else:
                                if _status_key(cid) != status_v:
                                    return False

                    return True

                def _count_values(*, ignore: str, field: str) -> dict[str, int]:
                    counts: dict[str, int] = {}
                    for c in courses:
                        if not _passes(c, ignore=ignore):
                            continue
                        v = str(c.get(field) or "").strip()
                        if not v:
                            continue
                        counts[v] = int(counts.get(v, 0)) + 1
                    return counts

                provider_counts = _count_values(ignore="provider", field="provider")
                category_counts = _count_values(ignore="category", field="category")
                level_counts = _count_values(ignore="level", field="level")

                # Preserve current selections even if they have a 0-count after other filters.
                selected_provider = str(provider_filter.value or "").strip()
                if selected_provider and selected_provider not in provider_counts:
                    provider_counts[selected_provider] = 0
                selected_category = str(category_filter.value or "").strip()
                if selected_category and selected_category not in category_counts:
                    category_counts[selected_category] = 0
                selected_level = str(level_filter.value or "").strip()
                if selected_level and selected_level not in level_counts:
                    level_counts[selected_level] = 0

                def _sorted_items(counts: dict[str, int]) -> list[tuple[str, int]]:
                    return sorted(counts.items(), key=lambda kv: (-int(kv[1]), str(kv[0]).lower()))

                provider_filter.options = {"": "Any provider", **{k: f"{k} ({n})" for k, n in _sorted_items(provider_counts)}}
                category_filter.options = {"": "Any category", **{k: f"{k} ({n})" for k, n in _sorted_items(category_counts)}}
                level_filter.options = {"": "Any level", **{k: f"{k} ({n})" for k, n in _sorted_items(level_counts)}}

                # Status counts (computed ignoring status itself).
                status_counts: dict[str, int] = {"not_tracked": 0, "interested": 0, "in_progress": 0, "completed": 0}
                for c in courses:
                    if not _passes(c, ignore="status"):
                        continue
                    cid = int(c.get("id") or 0)
                    key = _status_key(cid)
                    status_counts[key] = int(status_counts.get(key, 0)) + 1

                status_filter.options = {
                    "": "Any status",
                    "not_tracked": f"Not tracked ({status_counts.get('not_tracked', 0)})",
                    "interested": f"Interested ({status_counts.get('interested', 0)})",
                    "in_progress": f"In progress ({status_counts.get('in_progress', 0)})",
                    "completed": f"Completed ({status_counts.get('completed', 0)})",
                }

                if provider_filter.value and provider_filter.value not in provider_filter.options:
                    provider_filter.value = ""
                if category_filter.value and category_filter.value not in category_filter.options:
                    category_filter.value = ""
                if level_filter.value and level_filter.value not in level_filter.options:
                    level_filter.value = ""
                if status_filter.value and status_filter.value not in status_filter.options:
                    status_filter.value = ""

                provider_filter.update()
                category_filter.update()
                level_filter.update()
                status_filter.update()

            async def _load() -> None:
                nonlocal courses, tracking_by_course_id, review_summary_by_course_id, recommendation_summary_by_course_id
                nonlocal loading, loaded_once, visible_count
                if loading:
                    return
                loading = True
                visible_count = page_size
                refresh_btn.disable()
                meta.text = "Loading..."
                courses_list.refresh()
                try:
                    params: dict[str, Any] = {}
                    if q.value:
                        params["q"] = str(q.value)
                    if provider_filter.value:
                        params["provider"] = str(provider_filter.value)
                    if category_filter.value:
                        params["category"] = str(category_filter.value)
                    if level_filter.value:
                        params["level"] = str(level_filter.value)

                    courses, tracking_by_course_id = await load_courses_and_tracking(api=api, course_params=params or None)
                    review_summary_by_course_id = await load_review_summaries(
                        api=api,
                        course_ids=[int(c.get("id") or 0) for c in courses if int(c.get("id") or 0) > 0],
                    )
                    recommendation_summary_by_course_id = await load_recommendation_summaries(
                        api=api,
                        course_ids=[int(c.get("id") or 0) for c in courses if int(c.get("id") or 0) > 0],
                    )
                    _recompute_facet_options()
                    courses_list.refresh()
                    meta.text = f"{len(courses)} courses"
                except ApiError as exc:
                    ui.notify(str(exc), type="negative")
                    courses = []
                    tracking_by_course_id = {}
                    review_summary_by_course_id = {}
                    recommendation_summary_by_course_id = {}
                    _recompute_facet_options()
                    courses_list.refresh()
                    meta.text = "0 courses"
                finally:
                    loading = False
                    loaded_once = True
                    refresh_btn.enable()
                    courses_list.refresh()

            async def _reload_tracking_only() -> None:
                nonlocal tracking_by_course_id
                try:
                    tracking_by_course_id = await load_tracking_map(api=api)
                except ApiError as exc:
                    ui.notify(str(exc), type="negative")
                    tracking_by_course_id = {}
                    courses_list.refresh()
                    return
                _recompute_facet_options()
                courses_list.refresh()

            @guard_ui_action(title="Update status failed")
            async def _set_tracking(course_id: int, status: str) -> None:
                await api.post("/tracking", {"course_id": course_id, "status": status})
                await _reload_tracking_only()
                ui.notify("Updated status", type="positive")

            @guard_ui_action(title="Remove status failed")
            async def _clear_tracking(course_id: int) -> None:
                await api.post("/tracking/delete", {"course_id": course_id})
                await _reload_tracking_only()
                ui.notify("Removed status", type="positive")

            # Pre-build the Create dialog once so opening it is instant.
            create_dialog = ui.dialog()
            with create_dialog, ui.card().classes("lp-card lp-dialog w-[min(700px,95vw)]"):
                ui.label("Create Course").classes("text-xl font-semibold")

                create_title = ui.input("Title").props("clearable").classes("w-full")
                create_description = ui.textarea("Description").props("autogrow").classes("w-full")
                create_provider = ui.input("Provider").props("clearable").classes("w-full")
                create_category = ui.input("Category").props("clearable").classes("w-full")
                create_url = ui.input("URL").props("clearable").classes("w-full")

                with ui.expansion("More fields").props("dense"):
                    with ui.column().classes("w-full gap-3"):
                        create_level = ui.input("Level").props("clearable").classes("w-full")
                        create_duration_hours = ui.input("Duration hours").props("clearable").classes("w-full")

                with ui.row().classes("justify-end mt-4"):

                    @guard_ui_action(title="Create course failed")
                    async def _create_submit() -> None:
                        dh_raw = str(create_duration_hours.value or "")
                        dh = _parse_duration_hours(dh_raw)
                        if dh_raw.strip() and dh is None:
                            ui.notify("Duration hours must be a number", type="negative")
                            return
                        if not str(create_description.value or "").strip():
                            ui.notify("Description is required", type="negative")
                            return

                        payload = {
                            "title": str(create_title.value or ""),
                            "description": str(create_description.value or "").strip(),
                            "provider": str(create_provider.value or ""),
                            "category": str(create_category.value or ""),
                            "level": str(create_level.value or ""),
                            "duration_hours": dh,
                            "url": str(create_url.value or ""),
                        }
                        await api.post("/courses", payload)
                        ui.notify("Course created", type="positive")
                        create_dialog.close()
                        await _load()

                    ui.button("Create", on_click=_create_submit)
                    ui.button("Cancel", on_click=create_dialog.close).props("outline")

            def _open_create_dialog() -> None:
                create_title.value = ""
                create_description.value = ""
                create_provider.value = ""
                create_category.value = ""
                create_level.value = ""
                create_duration_hours.value = ""
                create_url.value = ""
                create_dialog.open()

            def _render_edit_course_dialog(course: dict[str, Any]) -> None:
                with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(700px,95vw)]"):
                    ui.label("Edit Course").classes("text-xl font-semibold")

                    course_id = int(course.get("id") or 0)
                    title = ui.input("Title", value=str(course.get("title") or "")).props("clearable").classes("w-full")
                    description = (
                        ui.textarea("Description", value=str(course.get("description") or ""))
                        .props("autogrow")
                        .classes("w-full")
                    )
                    provider_new = (
                        ui.input("Provider", value=str(course.get("provider") or "")).props("clearable").classes("w-full")
                    )
                    category_new = (
                        ui.input("Category", value=str(course.get("category") or "")).props("clearable").classes("w-full")
                    )
                    url = ui.input("URL", value=str(course.get("url") or "")).props("clearable").classes("w-full")

                    with ui.expansion("More fields").props("dense"):
                        with ui.column().classes("w-full gap-3"):
                            level_new = (
                                ui.input("Level", value=str(course.get("level") or "")).props("clearable").classes("w-full")
                            )
                            duration_hours = (
                                ui.input("Duration hours", value=str(course.get("duration_hours") or ""))
                                .props("clearable")
                                .classes("w-full")
                            )

                    with ui.row().classes("justify-end mt-4"):

                        @guard_ui_action(title="Save changes failed")
                        async def _save() -> None:
                            dh_raw = str(duration_hours.value or "")
                            dh = _parse_duration_hours(dh_raw)
                            if dh_raw.strip() and dh is None:
                                ui.notify("Duration hours must be a number", type="negative")
                                return
                            if not str(description.value or "").strip():
                                ui.notify("Description is required", type="negative")
                                return

                            payload = {
                                "title": str(title.value or ""),
                                "description": str(description.value or "").strip(),
                                "provider": str(provider_new.value or ""),
                                "category": str(category_new.value or ""),
                                "level": str(level_new.value or ""),
                                "duration_hours": dh,
                                "url": str(url.value or ""),
                            }
                            await api.put(f"/courses/{course_id}", payload)
                            ui.notify("Course updated", type="positive")
                            dialog.close()
                            await _load()

                        ui.button("Save", on_click=_save)
                        ui.button("Cancel", on_click=dialog.close).props("outline")

                dialog.open()

            async def _confirm_delete_course(course_id: int) -> None:
                with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog"):
                    ui.label("Delete this course?").classes("text-lg font-semibold")
                    ui.label("This cannot be undone.").classes("text-sm text-gray-600")
                    with ui.row().classes("justify-end mt-4"):

                        @guard_ui_action(title="Delete course failed")
                        async def _delete() -> None:
                            await api.delete(f"/courses/{course_id}")
                            ui.notify("Course deleted", type="positive")
                            dialog.close()
                            await _load()

                        ui.button("Delete", on_click=_delete).props("color=negative")
                        ui.button("Cancel", on_click=dialog.close).props("outline")
                dialog.open()

            @guard_ui_action(title="Load course details failed")
            async def _open_details(course_id: int, *, focus_reviews: bool = False) -> None:
                course, reviews_payload, recommendations_payload = await asyncio.gather(
                    api.get(f"/courses/{course_id}"),
                    api.get(f"/courses/{course_id}/reviews"),
                    api.get(f"/courses/{course_id}/recommendations"),
                )
                reviews = list(reviews_payload or [])
                recommendations = list(recommendations_payload or [])
                view_mode = _normalize_course_view_mode(focus_reviews)

                with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(800px,95vw)]"):
                    ui.label(course.get("title") or "").classes("text-xl font-semibold")
                    if str(course.get("description") or "").strip():
                        ui.label(str(course.get("description") or "")).classes("text-sm text-gray-600")
                    if view_mode != "reviews":
                        summary_label = _format_review_summary(review_summary_by_course_id.get(int(course_id)))
                        provider = str(course.get("provider") or "").strip()
                        category = str(course.get("category") or "").strip()
                        shared_by = str(course.get("created_by") or "").strip()

                        with ui.row().classes("items-center justify-between w-full mt-2"):
                            with ui.row().classes("items-center gap-2 flex-wrap"):
                                if provider:
                                    ui.label(provider).classes("lp-meta-chip")
                                if category:
                                    ui.label(category).classes("lp-meta-chip")
                                if shared_by:
                                    ui.label(f"Shared by {shared_by}").classes("text-xs").style("color: var(--lp-muted)")
                                if summary_label:
                                    ui.label(f"★ {summary_label}").classes("lp-meta-chip")
                                rec_badge = _format_recommendation_badge(
                                    recommendation_summary_by_course_id.get(int(course_id))
                                )
                                if rec_badge:
                                    ui.label(rec_badge).classes("lp-meta-chip")
                            if course.get("url"):
                                ui.button(
                                    "Open link",
                                    icon="open_in_new",
                                    on_click=lambda u=str(course.get("url")): ui.navigate.to(u, new_tab=True),
                                ).props("outline dense")

                        ui.separator()
                        if recommendations:
                            rec_by = sorted(
                                {
                                    str(r.get("created_by") or "").strip()
                                    for r in recommendations
                                    if isinstance(r, dict) and str(r.get("created_by") or "").strip()
                                }
                            )
                            if rec_by:
                                ui.label(f"Recommended by {', '.join(rec_by[:3])}").classes("text-xs").style(
                                    "color: var(--lp-muted)"
                                )
                        latest_activity: str | None = None
                        timestamps: list[str] = []
                        for row in list(reviews) + list(recommendations):
                            if not isinstance(row, dict):
                                continue
                            created_at = str(row.get("created_at") or "").strip()
                            if created_at:
                                timestamps.append(created_at)
                        if timestamps:
                            latest_activity = max(timestamps)
                        if latest_activity:
                            ui.label(f"Latest activity: {_format_short_date(latest_activity)}").classes("text-xs").style(
                                "color: var(--lp-muted)"
                            )

                    def _sync_summary_from_reviews(current_reviews: list[dict[str, Any]]) -> None:
                        ratings: list[int] = []
                        for r in list(current_reviews or []):
                            try:
                                ratings.append(int(r.get("rating") or 0))
                            except (TypeError, ValueError):
                                continue
                        if not ratings:
                            review_summary_by_course_id[int(course_id)] = {
                                "course_id": int(course_id),
                                "avg_rating": 0.0,
                                "review_count": 0,
                            }
                        else:
                            avg = float(sum(ratings)) / float(len(ratings))
                            review_summary_by_course_id[int(course_id)] = {
                                "course_id": int(course_id),
                                "avg_rating": float(avg),
                                "review_count": int(len(ratings)),
                            }

                    async def _save_review(rating: int, text: str) -> dict[str, Any]:
                        return await api.post(
                            f"/courses/{course_id}/reviews",
                            {"rating": int(rating), "text": str(text or "")},
                        )

                    async def _delete_review(review_id: int) -> bool:
                        await api.delete(f"/courses/{course_id}/reviews/{int(review_id)}")
                        return True

                    render_reviews_panel(
                        username=username,
                        is_admin=is_admin,
                        reviews=reviews,
                        section_title="Reviews",
                        empty_text="No reviews yet.",
                        on_save=_save_review,
                        on_delete=_delete_review,
                        format_date=_format_short_date,
                        on_changed=_sync_summary_from_reviews,
                    )

                    with ui.row().classes("justify-end mt-4"):
                        ui.button("Close", on_click=dialog.close).props("outline")

                dialog.open()

            @guard_ui_action(title="Recommend failed")
            async def _open_recommend_dialog(course_id: int) -> None:
                existing_note = ""
                try:
                    rows = await api.get(f"/courses/{int(course_id)}/recommendations")
                    for row in list(rows or []):
                        if not isinstance(row, dict):
                            continue
                        if str(row.get("created_by") or "") == username:
                            existing_note = str(row.get("note") or "")
                            break
                except ApiError:
                    existing_note = ""

                with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(600px,95vw)]"):
                    ui.label("Recommend course").classes("text-lg font-semibold")
                    note = ui.textarea("Why this helps (optional)", value=existing_note).props("autogrow").classes("w-full")
                    with ui.row().classes("justify-end mt-4"):

                        @guard_ui_action(title="Recommend failed")
                        async def _save_recommendation() -> None:
                            await api.post(
                                f"/courses/{int(course_id)}/recommendations",
                                {"note": str(note.value or "").strip()},
                            )
                            ui.notify("Recommendation saved", type="positive")
                            dialog.close()
                            await _load()

                        ui.button("Save", on_click=_save_recommendation)
                        ui.button("Cancel", on_click=dialog.close).props("outline")
                dialog.open()

            @ui.refreshable
            def courses_list() -> None:
                nonlocal visible_count
                needle = str(q.value or "").strip().lower()
                provider_v = str(provider_filter.value or "").strip().lower()
                category_v = str(category_filter.value or "").strip().lower()
                level_v = str(level_filter.value or "").strip().lower()
                status_v = str(status_filter.value or "")
                sort_v = str(sort_filter.value or "")
                scope_v = str(scope_filter.value or "all")

                shown = courses
                if needle:
                    shown = [
                        c
                        for c in shown
                        if needle in str(c.get("title") or "").lower() or needle in str(c.get("description") or "").lower()
                    ]
                if provider_v:
                    shown = [c for c in shown if provider_v == str(c.get("provider") or "").strip().lower()]
                if category_v:
                    shown = [c for c in shown if category_v == str(c.get("category") or "").strip().lower()]
                if level_v:
                    shown = [c for c in shown if level_v == str(c.get("level") or "").strip().lower()]

                if status_v:
                    if status_v == "not_tracked":
                        shown = [c for c in shown if int(c.get("id") or 0) not in tracking_by_course_id]
                    else:
                        shown = [
                            c
                            for c in shown
                            if str((tracking_by_course_id.get(int(c.get("id") or 0)) or {}).get("status") or "") == status_v
                        ]

                if scope_v == "tracked":
                    shown = [c for c in shown if int(c.get("id") or 0) in tracking_by_course_id]

                if sort_v:
                    if sort_v == "title_az":
                        shown = sorted(shown, key=lambda c: str(c.get("title") or "").strip().lower())
                    elif sort_v == "newest":

                        def _created_key(c: dict[str, Any]) -> tuple[datetime, int]:
                            # Prefer parsed timestamps; fall back to id for stability.
                            dt = _parse_iso_datetime(c.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)
                            return (dt, int(c.get("id") or 0))

                        shown = sorted(shown, key=_created_key, reverse=True)
                    elif sort_v == "top_rated":

                        def _rating_key(c: dict[str, Any]) -> tuple[float, int, str]:
                            cid = int(c.get("id") or 0)
                            s = review_summary_by_course_id.get(cid) or {}
                            try:
                                avg = float(s.get("avg_rating") or 0.0)
                            except (TypeError, ValueError):
                                avg = 0.0
                            try:
                                cnt = int(s.get("review_count") or 0)
                            except (TypeError, ValueError):
                                cnt = 0
                            title = str(c.get("title") or "").strip().lower()
                            return (avg, cnt, title)

                        shown = sorted(shown, key=_rating_key, reverse=True)
                    elif sort_v == "most_reviewed":

                        def _count_key(c: dict[str, Any]) -> tuple[int, float, str]:
                            cid = int(c.get("id") or 0)
                            s = review_summary_by_course_id.get(cid) or {}
                            try:
                                cnt = int(s.get("review_count") or 0)
                            except (TypeError, ValueError):
                                cnt = 0
                            try:
                                avg = float(s.get("avg_rating") or 0.0)
                            except (TypeError, ValueError):
                                avg = 0.0
                            title = str(c.get("title") or "").strip().lower()
                            return (cnt, avg, title)

                        shown = sorted(shown, key=_count_key, reverse=True)

                with ui.column().classes("w-full gap-3"):
                    if loading or not loaded_once:
                        render_card_skeletons(count=4)
                        return

                    if not shown:
                        any_filters = any(
                            [
                                str(q.value or "").strip(),
                                str(provider_filter.value or "").strip(),
                                str(category_filter.value or "").strip(),
                                str(level_filter.value or "").strip(),
                                str(status_filter.value or "").strip(),
                            ]
                        )

                        if scope_v == "tracked" and any_filters is False:
                            ui.label("No tracked courses yet.").classes("text-sm").style("color: var(--lp-muted)")
                            ui.label("Browse courses and set a status to start tracking.").classes("text-sm").style(
                                "color: var(--lp-muted)"
                            )
                            with ui.row().classes("items-center gap-2"):
                                ui.button(
                                    "Browse all courses",
                                    on_click=lambda: setattr(scope_filter, "value", "all") or _refresh_list(),
                                ).props("outline")
                                ui.button("Refresh", on_click=_load).props("outline")
                            return

                        if not courses and not any_filters:
                            ui.label("No courses yet.").classes("text-sm").style("color: var(--lp-muted)")
                            ui.label("Share the first course to get started.").classes("text-sm").style(
                                "color: var(--lp-muted)"
                            )
                            with ui.row().classes("items-center gap-2"):
                                ui.button("Share a course", on_click=lambda: _open_create_dialog()).props("outline")
                                ui.button("Refresh", on_click=_load).props("outline")
                            return

                        ui.label("No courses match your filters.").classes("text-sm").style("color: var(--lp-muted)")
                        if any_filters:
                            ui.label("Try resetting filters to broaden results.").classes("text-xs").style(
                                "color: var(--lp-muted)"
                            )
                        with ui.row().classes("items-center gap-2"):
                            ui.button("Reset all", on_click=_reset_all).props("outline")
                            ui.button("Refresh", on_click=_load).props("outline")
                        return

                    shown_total = len(shown)
                    shown_page = shown[: max(0, int(visible_count))]

                    for c in shown_page:
                        course_id = int(c.get("id") or 0)
                        tracked = tracking_by_course_id.get(course_id)
                        can_edit = is_admin or (str(c.get("created_by") or "") == username)
                        url = str(c.get("url") or "").strip()

                        async def _view(_cid: int = course_id) -> None:
                            await _open_details(_cid)

                        async def _review(_cid: int = course_id) -> None:
                            await _open_details(_cid, focus_reviews=True)

                        async def _recommend(_cid: int = course_id) -> None:
                            await _open_recommend_dialog(_cid)

                        def _copy_link(*, _url: str = url) -> None:
                            ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(_url)});")
                            ui.notify("Link copied", type="positive")

                        async def _do_delete(_cid: int = course_id) -> None:
                            await _confirm_delete_course(_cid)

                        st = _status_for_card(tracked)
                        st_cls = f" lp-course-card--{st}" if st else ""
                        with ui.card().classes(f"w-full lp-course-card lp-card--hover{st_cls}"):
                            with ui.row().classes("items-start justify-between w-full"):
                                with ui.column().classes("gap-1"):
                                    title = str(c.get("title") or "")
                                    rating_badge = _format_rating_badge(review_summary_by_course_id.get(course_id))
                                    rec_badge = _format_recommendation_badge(recommendation_summary_by_course_id.get(course_id))
                                    created_at = _parse_iso_datetime(c.get("created_at"))
                                    updated_at = _parse_iso_datetime(c.get("updated_at"))
                                    is_updated = (
                                        _is_recent(updated_at)
                                        and created_at is not None
                                        and updated_at is not None
                                        and updated_at > created_at
                                    )
                                    is_new = (not is_updated) and _is_recent(created_at)
                                    with ui.element("div").classes("lp-card-topright"):
                                        if is_new:
                                            ui.label("New").classes("lp-chip lp-chip--sky")
                                        elif is_updated:
                                            ui.label("Updated").classes("lp-chip lp-chip--teal")
                                        if rating_badge:
                                            ui.label(rating_badge).classes("lp-meta-chip")
                                        if rec_badge:
                                            ui.label(rec_badge).classes("lp-meta-chip")
                                        with ui.dropdown_button("", icon="more_vert", auto_close=True).props("dense flat"):
                                            ui.menu_item("Review", _review)
                                            ui.menu_item("Recommend", _recommend)
                                            if url:
                                                ui.menu_item("Copy link", _copy_link)
                                            if can_edit:
                                                ui.menu_item("Edit", lambda course=c: _render_edit_course_dialog(course))
                                                ui.menu_item("Delete", _do_delete)

                                    ui.label(title).classes("text-lg font-semibold")
                                    shared_by = str(c.get("created_by") or "").strip()
                                    if shared_by:
                                        ui.label(f"Shared by {shared_by}").classes("text-xs").style("color: var(--lp-muted)")
                                    if str(c.get("description") or "").strip():
                                        ui.label(str(c.get("description") or "")).classes("text-sm text-gray-600")
                                    with ui.row().classes("items-center gap-2 flex-wrap"):
                                        chips: list[str] = []
                                        if str(c.get("provider") or "").strip():
                                            chips.append(str(c.get("provider") or "").strip())
                                        if str(c.get("category") or "").strip():
                                            chips.append(str(c.get("category") or "").strip())

                                        max_chips = 2
                                        for chip in chips[:max_chips]:
                                            ui.label(chip).classes("lp-meta-chip")
                                        if len(chips) > max_chips:
                                            ui.label(f"+{len(chips) - max_chips}").classes("lp-meta-chip")

                                        ui.label(tracking_label((tracked or {}).get("status"))).classes(
                                            tracking_chip_class((tracked or {}).get("status"))
                                        )

                                with ui.column().classes("items-end gap-2"):
                                    with ui.row().classes("items-center gap-2"):
                                        ui.button("", icon="visibility", on_click=_view).props("outline dense").tooltip("View")

                                        current_status = str((tracked or {}).get("status") or "")
                                        options_map = {
                                            "": "Not tracked",
                                            **{k: v for k, v in TRACKING_STATUS_OPTIONS},
                                        }
                                        status_select = ui.select(
                                            options=options_map,
                                            value=current_status,
                                            label=None,
                                        ).props("dense")
                                        status_select.style("min-width: 170px")
                                        status_select.props("use-input hide-selected fill-input")
                                        status_select.tooltip("Status")

                                        async def _on_status_change(
                                            e: Any, _cid: int = course_id, _select=status_select
                                        ) -> None:
                                            _select.disable()
                                            try:
                                                raw = e
                                                if not isinstance(e, (str, int, float, bool, dict)) and e is not None:
                                                    raw = getattr(e, "value", None)
                                                    if raw is None:
                                                        raw = getattr(e, "args", None)

                                                # NiceGUI/Quasar may emit dicts like {"value": 1, "label": "Interested"}.
                                                if isinstance(raw, dict):
                                                    if raw.get("value") in options_map:
                                                        value = str(raw.get("value") or "")
                                                    elif "label" in raw:
                                                        label = str(raw.get("label") or "").strip().lower()
                                                        value = ""
                                                        for key, opt_label in options_map.items():
                                                            if label and label == str(opt_label).strip().lower():
                                                                value = str(key)
                                                                break
                                                    else:
                                                        value = ""
                                                else:
                                                    value = str(raw or _select.value or "")

                                                if not value:
                                                    # Keep the control in sync with "not tracked".
                                                    _select.value = ""
                                                    _select.update()
                                                    if int(_cid) in tracking_by_course_id:
                                                        await _clear_tracking(_cid)
                                                    return
                                                if value not in {"interested", "in_progress", "completed"}:
                                                    ui.notify(f"Invalid status: {value}", type="negative")
                                                    return
                                                # Quasar may emit option objects; force the model to the backend key
                                                # so the select doesn't snap back on the next render.
                                                _select.value = value
                                                _select.update()
                                                await _set_tracking(_cid, value)
                                            finally:
                                                _select.enable()

                                        status_select.on("update:model-value", _on_status_change)

                    if shown_total > len(shown_page):
                        with ui.row().classes("items-center justify-center mt-2"):

                            def _load_more() -> None:
                                nonlocal visible_count
                                visible_count = min(shown_total, int(visible_count) + page_size)
                                courses_list.refresh()

                            ui.button(
                                f"Load more ({len(shown_page)}/{shown_total})",
                                on_click=_load_more,
                            ).props("outline")

            def _refresh_list(*_: Any) -> None:
                nonlocal visible_count
                visible_count = page_size
                _recompute_facet_options()
                active_filters.refresh()
                courses_list.refresh()

            def _clear_filter_values() -> None:
                q.value = ""
                provider_filter.value = ""
                category_filter.value = ""
                level_filter.value = ""
                status_filter.value = ""
                sort_filter.value = ""
                q.update()
                provider_filter.update()
                category_filter.update()
                level_filter.update()
                status_filter.update()
                sort_filter.update()
                active_filters.refresh()
                courses_list.refresh()

            @guard_ui_action(title="Reset filters failed")
            async def _reset_all() -> None:
                _clear_filter_values()
                await _load()

            q.on("update:model-value", _refresh_list)

            @ui.refreshable
            def active_filters() -> None:
                """Render removable filter chips above the results list."""

                def _chip(label: str, on_clear: Any) -> None:
                    with ui.row().classes("items-center"):
                        with ui.element("div").classes("lp-filter-chip"):
                            ui.label(label)
                            ui.button("×", on_click=on_clear).props("dense flat")

                any_chip = False
                with ui.row().classes("items-center gap-2 w-full"):
                    if str(scope_filter.value or "") == "tracked":
                        any_chip = True

                        def _clear_scope() -> None:
                            scope_filter.value = "all"
                            scope_filter.update()
                            active_filters.refresh()
                            courses_list.refresh()

                        _chip("View: Tracked", _clear_scope)

                    if str(q.value or "").strip():
                        any_chip = True

                        def _clear_q() -> None:
                            q.value = ""
                            q.update()
                            active_filters.refresh()
                            courses_list.refresh()

                        _chip(f"Search: {str(q.value or '').strip()}", _clear_q)

                    if str(provider_filter.value or "").strip():
                        any_chip = True

                        def _clear_provider() -> None:
                            provider_filter.value = ""
                            provider_filter.update()
                            active_filters.refresh()
                            courses_list.refresh()

                        _chip(f"Provider: {provider_filter.value}", _clear_provider)

                    if str(category_filter.value or "").strip():
                        any_chip = True

                        def _clear_category() -> None:
                            category_filter.value = ""
                            category_filter.update()
                            active_filters.refresh()
                            courses_list.refresh()

                        _chip(f"Category: {category_filter.value}", _clear_category)

                    if str(level_filter.value or "").strip():
                        any_chip = True

                        def _clear_level() -> None:
                            level_filter.value = ""
                            level_filter.update()
                            active_filters.refresh()
                            courses_list.refresh()

                        _chip(f"Level: {level_filter.value}", _clear_level)

                    if str(status_filter.value or "").strip():
                        any_chip = True
                        label = str(status_filter.options.get(status_filter.value) or status_filter.value)

                        def _clear_status() -> None:
                            status_filter.value = ""
                            status_filter.update()
                            active_filters.refresh()
                            courses_list.refresh()

                        _chip(f"Status: {label}", _clear_status)

                if not any_chip:
                    return

            def _render_rail() -> None:
                nonlocal provider_filter, category_filter, level_filter, status_filter, refresh_btn
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label("Filters").classes("text-md font-semibold")
                    with ui.row().classes("items-center gap-2"):
                        refresh_btn = ui.button("Refresh", on_click=_load).props("outline dense")

                ui.label("Tip: use filters to narrow results.").classes("text-xs").style("color: var(--lp-muted)")

                provider_filter = ui.select({"": "Any provider"}, label="Provider", value="").props("dense").classes("w-full")
                category_filter = ui.select({"": "Any category"}, label="Category", value="").props("dense").classes("w-full")
                level_filter = ui.select({"": "Any level"}, label="Level", value="").props("dense").classes("w-full")
                status_filter = (
                    ui.select(
                        {"": "Any status", "not_tracked": "Not tracked", **{k: v for k, v in TRACKING_STATUS_OPTIONS}},
                        label="My status",
                        value="",
                    )
                    .props("dense")
                    .classes("w-full")
                )
                provider_filter.on("update:model-value", _refresh_list)
                category_filter.on("update:model-value", _refresh_list)
                level_filter.on("update:model-value", _refresh_list)
                status_filter.on("update:model-value", _refresh_list)
                # Push the reset action to the bottom so it feels anchored.
                ui.element("div").style("flex: 1")
                ui.button("Clear", on_click=_reset_all).props("outline dense").classes("w-full")

            def _render_main() -> None:
                active_filters()
                courses_list()

            render_split_layout(rail=_render_rail, main=_render_main, rail_classes="lp-rail--bar")

            await _load()
            if initial_course_id > 0:
                await _open_details(initial_course_id, focus_reviews=initial_focus_reviews)
                if isinstance(intent, dict):
                    try:
                        if int(intent.get("course_id") or 0) == int(initial_course_id):
                            app.storage.user.pop("courses_open_intent", None)
                    except (TypeError, ValueError):
                        pass
                if isinstance(nav_intent, dict):
                    try:
                        if int(nav_intent.get("course_id") or 0) == int(initial_course_id):
                            pop_course_intent(username=username)
                    except (TypeError, ValueError):
                        pass
