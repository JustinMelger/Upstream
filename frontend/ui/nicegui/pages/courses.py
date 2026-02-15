"""Courses browse/admin page for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_container, render_shell, render_split_layout
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.status_chips import tracking_chip_class, tracking_label, TRACKING_STATUS_OPTIONS
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.services.courses_service import load_courses_and_tracking, load_review_summaries, load_tracking_map


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


def _status_for_card(tracked: dict[str, Any] | None) -> str:
    """Return a stable tracking status string for card styling."""
    v = str((tracked or {}).get("status") or "").strip()
    if v in {"interested", "in_progress", "completed"}:
        return v
    return ""


def _parse_iso_datetime(value: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp into an aware datetime (UTC when possible)."""
    s = str(value or "").strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _is_recent(dt: datetime | None, *, days: int = 7) -> bool:
    """Return True when dt is within the last N days."""
    if dt is None:
        return False
    now = datetime.now(timezone.utc)
    return dt >= (now - timedelta(days=int(days)))


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
            page_size = 10
            visible_count = page_size

            with ui.row().classes("lp-topbar"):
                q = ui.input("Search courses").props("clearable debounce=300").style("flex: 1")
                with ui.row().classes("items-center gap-2").style("margin-left: auto"):
                    ui.button("Share", on_click=lambda: _open_create_dialog()).props("dense")
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
                    meta = ui.label("").classes("lp-topbar-meta")

            loading = False
            loaded_once = False

            provider_filter: Any = None
            category_filter: Any = None
            level_filter: Any = None
            status_filter: Any = None
            refresh_btn: Any = None

            def _update_facet_options() -> None:
                providers = sorted(
                    {str(c.get("provider") or "").strip() for c in courses if str(c.get("provider") or "").strip()}
                )
                categories = sorted(
                    {str(c.get("category") or "").strip() for c in courses if str(c.get("category") or "").strip()}
                )
                levels = sorted({str(c.get("level") or "").strip() for c in courses if str(c.get("level") or "").strip()})

                provider_filter.options = {"": "Any provider", **{p: p for p in providers}}
                category_filter.options = {"": "Any category", **{c: c for c in categories}}
                level_filter.options = {"": "Any level", **{l: l for l in levels}}

                if provider_filter.value and provider_filter.value not in provider_filter.options:
                    provider_filter.value = ""
                if category_filter.value and category_filter.value not in category_filter.options:
                    category_filter.value = ""
                if level_filter.value and level_filter.value not in level_filter.options:
                    level_filter.value = ""

                provider_filter.update()
                category_filter.update()
                level_filter.update()

            async def _load() -> None:
                nonlocal courses, tracking_by_course_id, review_summary_by_course_id, loading, loaded_once, visible_count
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
                    _update_facet_options()
                    courses_list.refresh()
                    meta.text = f"{len(courses)} courses"
                except ApiError as exc:
                    ui.notify(str(exc), type="negative")
                    courses = []
                    tracking_by_course_id = {}
                    review_summary_by_course_id = {}
                    _update_facet_options()
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
                course, reviews_payload = await asyncio.gather(
                    api.get(f"/courses/{course_id}"),
                    api.get(f"/courses/{course_id}/reviews"),
                )
                reviews = list(reviews_payload or [])

                with ui.dialog() as dialog, ui.card().classes("lp-card lp-dialog w-[min(800px,95vw)]"):
                    ui.label(course.get("title") or "").classes("text-xl font-semibold")
                    if str(course.get("description") or "").strip():
                        ui.label(str(course.get("description") or "")).classes("text-sm text-gray-600")
                    summary_el = ui.label("").classes("text-xs text-gray-600")
                    summary_label = _format_review_summary(review_summary_by_course_id.get(int(course_id)))
                    summary_el.text = f"Reviews: {summary_label}" if summary_label else ""
                    ui.label(
                        f"{course.get('provider') or ''} · {course.get('category') or ''} · {course.get('level') or ''}"
                    ).classes("text-sm text-gray-600")

                    if course.get("duration_hours") is not None:
                        ui.label(f"Duration: {course.get('duration_hours')}h").classes("text-sm")

                    if course.get("url"):
                        ui.link("Open link", str(course.get("url"))).props("target=_blank").classes("text-sm")

                    ui.separator()
                    reviews_anchor_id = f"course-reviews-{int(course_id)}"
                    ui.html(f'<div id="{reviews_anchor_id}"></div>')
                    ui.label("Reviews").classes("text-lg font-semibold")

                    def _find_my_review() -> dict[str, Any] | None:
                        for r in reviews:
                            if str(r.get("created_by") or "") == username:
                                return dict(r)
                        return None

                    my_review = _find_my_review()

                    def _update_summary_from_reviews() -> None:
                        """Update the course-level summary cache from the current reviews list."""
                        ratings: list[int] = []
                        for r in list(reviews or []):
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
                            summary_el.text = ""
                            return
                        avg = float(sum(ratings)) / float(len(ratings))
                        review_summary_by_course_id[int(course_id)] = {
                            "course_id": int(course_id),
                            "avg_rating": float(avg),
                            "review_count": int(len(ratings)),
                        }
                        summary_el.text = f"Reviews: {_format_review_summary(review_summary_by_course_id.get(int(course_id)))}"

                    @guard_ui_action(title="Delete review failed")
                    async def _delete_review(review_id: int) -> None:
                        nonlocal reviews, my_review
                        await api.delete(f"/courses/{course_id}/reviews/{int(review_id)}")
                        reviews = [r for r in reviews if int(r.get("id") or 0) != int(review_id)]
                        my_review = _find_my_review()
                        _update_summary_from_reviews()
                        if my_review is None:
                            rating_in.value = 5
                            text_in.value = ""
                            my_review_label.text = "Add a review"
                        reviews_list.refresh()
                        ui.notify("Review deleted", type="positive")

                    @ui.refreshable
                    def reviews_list() -> None:
                        with ui.column().classes("w-full gap-2"):
                            if not reviews:
                                ui.label("No reviews yet.").classes("text-sm text-gray-600")
                            for r in reviews[:10]:
                                try:
                                    rating = int(r.get("rating") or 0)
                                except (TypeError, ValueError):
                                    rating = 0
                                who = str(r.get("created_by") or "").strip()
                                when = str(r.get("created_at") or "").strip()
                                text = str(r.get("text") or "").strip()
                                with ui.card().classes("lp-card w-full"):
                                    with ui.row().classes("items-start justify-between w-full"):
                                        ui.label(f"Rating: {max(1, min(5, rating))}/5 · {who}").classes("text-sm font-semibold")
                                        can_delete = is_admin or (who == username)
                                        if can_delete:

                                            async def _do_delete(_rid: int = int(r.get("id") or 0)) -> None:
                                                await _delete_review(_rid)

                                            ui.button("Delete", on_click=_do_delete).props("dense color=negative outline")
                                    if when:
                                        ui.label(when).classes("text-xs text-gray-600")
                                    if text:
                                        ui.label(text).classes("text-sm text-gray-600")

                    reviews_list()

                    my_review_label = ui.label("Your review" if my_review else "Add a review").classes(
                        "text-md font-semibold mt-2"
                    )
                    rating_in = ui.select(
                        {1: "1", 2: "2", 3: "3", 4: "4", 5: "5"},
                        value=int((my_review or {}).get("rating") or 5),
                        label="Rating",
                    ).props("dense")
                    text_in = (
                        ui.textarea("Comment (optional)", value=str((my_review or {}).get("text") or ""))
                        .props("autogrow")
                        .classes("w-full")
                    )

                    @guard_ui_action(title="Review submit failed")
                    async def _submit_review() -> None:
                        saved = await api.post(
                            f"/courses/{course_id}/reviews",
                            {"rating": int(rating_in.value or 0), "text": str(text_in.value or "")},
                        )
                        ui.notify("Review saved", type="positive")
                        # Update the in-memory list so we don't have to reload the full courses list.
                        try:
                            saved_id = int((saved or {}).get("id") or 0)
                        except (TypeError, ValueError):
                            saved_id = 0
                        new_reviews: list[dict[str, Any]] = []
                        for r in reviews:
                            if str(r.get("created_by") or "") == username:
                                continue
                            if saved_id:
                                try:
                                    if int(r.get("id") or 0) == saved_id:
                                        continue
                                except (TypeError, ValueError):
                                    pass
                            new_reviews.append(dict(r))
                        if isinstance(saved, dict):
                            new_reviews.insert(0, dict(saved))
                        reviews[:] = new_reviews
                        _update_summary_from_reviews()
                        my_review_label.text = "Your review" if _find_my_review() else "Add a review"
                        reviews_list.refresh()

                    with ui.row().classes("justify-end mt-2"):
                        ui.button("Save review", on_click=_submit_review).props("outline")

                    with ui.row().classes("justify-end mt-4"):
                        ui.button("Close", on_click=dialog.close).props("outline")

                dialog.open()
                if focus_reviews:
                    # Allow the dialog to render before scrolling.
                    ui.timer(
                        0.05,
                        lambda _id=reviews_anchor_id: ui.run_javascript(
                            f"document.getElementById('{_id}')?.scrollIntoView({{behavior: 'smooth', block: 'start'}});"
                        ),
                        once=True,
                    )

            @ui.refreshable
            def courses_list() -> None:
                nonlocal visible_count
                needle = str(q.value or "").strip().lower()
                provider_v = str(provider_filter.value or "").strip().lower()
                category_v = str(category_filter.value or "").strip().lower()
                level_v = str(level_filter.value or "").strip().lower()
                status_v = str(status_filter.value or "")
                sort_v = str(sort_filter.value or "")

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
                        st = _status_for_card(tracked)
                        st_cls = f" lp-course-card--{st}" if st else ""
                        with ui.card().classes(f"w-full lp-course-card lp-card--hover{st_cls}"):
                            with ui.row().classes("items-start justify-between w-full"):
                                with ui.column().classes("gap-1"):
                                    title = str(c.get("title") or "")
                                    rating_badge = _format_rating_badge(review_summary_by_course_id.get(course_id))
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
                                        if can_edit:
                                            with ui.dropdown_button("", icon="more_vert", auto_close=True).props("dense flat"):
                                                ui.menu_item(
                                                    "Edit",
                                                    on_click=lambda course=c: _render_edit_course_dialog(course),
                                                )

                                                async def _do_delete(_cid: int = course_id) -> None:
                                                    await _confirm_delete_course(_cid)

                                                ui.menu_item("Delete", on_click=_do_delete)

                                    ui.label(title).classes("text-lg font-semibold")
                                    if str(c.get("description") or "").strip():
                                        ui.label(str(c.get("description") or "")).classes("text-sm text-gray-600")
                                    with ui.row().classes("items-center gap-2 flex-wrap"):
                                        shared_by = str(c.get("created_by") or "").strip()
                                        if shared_by:
                                            ui.label(f"Shared by {shared_by}").classes("text-xs").style(
                                                "color: var(--lp-muted)"
                                            )

                                        chips: list[str] = []
                                        if str(c.get("provider") or "").strip():
                                            chips.append(str(c.get("provider") or "").strip())
                                        if str(c.get("category") or "").strip():
                                            chips.append(str(c.get("category") or "").strip())

                                        max_chips = 3
                                        for chip in chips[:max_chips]:
                                            ui.label(chip).classes("lp-meta-chip")
                                        if len(chips) > max_chips:
                                            ui.label(f"+{len(chips) - max_chips}").classes("lp-meta-chip")

                                        ui.label(tracking_label((tracked or {}).get("status"))).classes(
                                            tracking_chip_class((tracked or {}).get("status"))
                                        )

                                with ui.column().classes("items-end gap-2"):
                                    with ui.row().classes("items-center"):

                                        async def _view(_cid: int = course_id) -> None:
                                            await _open_details(_cid)

                                        ui.button("View", on_click=_view).props("outline")

                                        async def _review(_cid: int = course_id) -> None:
                                            await _open_details(_cid, focus_reviews=True)

                                        ui.button("Review", on_click=_review).props("outline")

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
