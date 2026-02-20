"""Courses browse/admin page for the NiceGUI frontend."""

from __future__ import annotations

from datetime import timezone
from typing import Any

from nicegui import app, ui

from frontend.ui.nicegui.components.layout import render_container, render_shell, render_split_layout
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.navigation_intents import get_course_intent, pop_course_intent
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.courses.actions import build_course_card_actions
from frontend.ui.nicegui.pages.courses.controller import CoursesPageController
from frontend.ui.nicegui.pages.courses.detail_flow import open_course_details_dialog
from frontend.ui.nicegui.pages.courses.dialogs import (
    build_share_course_dialog,
    open_delete_course_dialog,
    open_edit_course_dialog,
    open_recommend_course_dialog,
)
from frontend.ui.nicegui.pages.courses.filters import build_list_query_params, normalize_courses_filter_values
from frontend.ui.nicegui.pages.courses.reducers import (
    build_count_options,
    build_status_options as _build_status_options,
    compute_facet_counts,
    filter_courses,
    sort_courses,
)
from frontend.ui.nicegui.pages.courses.route_init import intent_matches_course, resolve_courses_route_init
from frontend.ui.nicegui.pages.courses.sections import (
    render_active_filter_chips,
    render_course_card,
    render_courses_empty_state,
    render_filters_rail,
    render_load_more_control,
)
from frontend.ui.nicegui.pages.courses.state import CoursesPageState, CoursesPageUiState
from frontend.ui.nicegui.pages.courses.transitions import (
    apply_optimistic_tracking_clear,
    apply_optimistic_tracking_set,
    begin_courses_load,
    clear_courses_state_on_load_error,
    finalize_courses_load,
    rollback_optimistic_tracking,
)
from frontend.ui.nicegui.pages.courses.ui_glue import (
    build_active_filter_chips,
    compute_courses_meta_text,
    compute_expanded_visible_count,
    default_courses_filter_reset_state,
    resolve_tracking_status_value,
)
from frontend.ui.nicegui.pages.courses.view_model import map_course_card_view


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


_parse_iso_datetime = parse_iso_datetime


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
        controller = CoursesPageController(api=api)

        with render_container():
            page_state = CoursesPageState()
            ui_state = CoursesPageUiState()

            request = getattr(ui.context.client, "request", None)
            intent = app.storage.user.get("courses_open_intent")
            nav_intent = get_course_intent(username=username)
            route_init = resolve_courses_route_init(
                request=request,
                storage_intent=intent if isinstance(intent, dict) else None,
                nav_intent=nav_intent if isinstance(nav_intent, dict) else None,
            )

            with ui.row().classes("lp-topbar"):
                q = ui.input("Search courses").props("clearable debounce=300").style("flex: 1")
                with ui.row().classes("items-center gap-2").style("margin-left: auto"):
                    ui.button("Share", on_click=lambda: _open_create_dialog()).props("dense")
                    scope_filter = (
                        ui.radio(
                            {"all": "All", "tracked": "Tracked"},
                            value=route_init.initial_scope,
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
                normalized = normalize_courses_filter_values(
                    scope_value=str(scope_filter.value or "all"),
                    search_value=str(q.value or ""),
                    provider_value=str(provider_filter.value or ""),
                    category_value=str(category_filter.value or ""),
                    level_value=str(level_filter.value or ""),
                    status_value=str(status_filter.value or ""),
                    sort_value=str(sort_filter.value or ""),
                )
                provider_counts, category_counts, level_counts, status_counts = compute_facet_counts(
                    courses=page_state.courses,
                    tracking_by_course_id=page_state.tracking_by_course_id,
                    scope_value=normalized.scope,
                    needle=normalized.search,
                    provider_value=normalized.provider,
                    category_value=normalized.category,
                    level_value=normalized.level,
                    status_value=normalized.status,
                )

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

                provider_filter.options = build_count_options(any_label="Any provider", counts=provider_counts)
                category_filter.options = build_count_options(any_label="Any category", counts=category_counts)
                level_filter.options = build_count_options(any_label="Any level", counts=level_counts)
                status_filter.options = _build_status_options(status_counts=status_counts)

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
                if ui_state.loading:
                    return
                ok = False
                load_start = begin_courses_load(page_size=ui_state.page_size)
                ui_state.loading = load_start.loading
                ui_state.visible_count = load_start.visible_count
                refresh_btn.disable()
                meta.text = load_start.meta_text
                courses_list.refresh()
                try:
                    params = build_list_query_params(
                        search_value=str(q.value or ""),
                        provider_value=str(provider_filter.value or ""),
                        category_value=str(category_filter.value or ""),
                        level_value=str(level_filter.value or ""),
                    )

                    bundle = await controller.load_list_bundle(params=params or None)
                    page_state.courses = list(bundle.courses or [])
                    page_state.tracking_by_course_id = dict(bundle.tracking_by_course_id or {})
                    page_state.review_summary_by_course_id = dict(bundle.review_summary_by_course_id or {})
                    page_state.recommendation_summary_by_course_id = dict(bundle.recommendation_summary_by_course_id or {})
                    _recompute_facet_options()
                    courses_list.refresh()
                    ok = True
                except ApiError as exc:
                    safe_notify(str(exc), type="negative")
                    clear_courses_state_on_load_error(state=page_state)
                    _recompute_facet_options()
                    courses_list.refresh()
                finally:
                    load_done = finalize_courses_load(ok=ok, course_count=len(page_state.courses))
                    meta.text = compute_courses_meta_text(course_count=len(page_state.courses))
                    ui_state.loading = load_done.loading
                    ui_state.loaded_once = load_done.loaded_once
                    refresh_btn.enable()
                    courses_list.refresh()

            async def _reload_tracking_only() -> bool:
                try:
                    page_state.tracking_by_course_id = await controller.reload_tracking()
                except ApiError as exc:
                    safe_notify(str(exc), type="negative")
                    page_state.tracking_by_course_id = {}
                    courses_list.refresh()
                    return False
                _recompute_facet_options()
                courses_list.refresh()
                return True

            @guard_ui_action(title="Update status failed")
            async def _set_tracking(course_id: int, status: str) -> bool:
                snapshot = apply_optimistic_tracking_set(
                    state=page_state,
                    course_id=int(course_id),
                    status=str(status),
                )
                courses_list.refresh()
                try:
                    await api.post("/tracking", {"course_id": course_id, "status": status})
                    ok = await _reload_tracking_only()
                    if ok:
                        safe_notify("Updated status", type="positive")
                        return True
                    rollback_optimistic_tracking(state=page_state, snapshot=snapshot)
                    courses_list.refresh()
                    return False
                except Exception:
                    rollback_optimistic_tracking(state=page_state, snapshot=snapshot)
                    courses_list.refresh()
                    raise

            @guard_ui_action(title="Remove status failed")
            async def _clear_tracking(course_id: int) -> bool:
                snapshot = apply_optimistic_tracking_clear(state=page_state, course_id=int(course_id))
                courses_list.refresh()
                try:
                    await api.post("/tracking/delete", {"course_id": course_id})
                    ok = await _reload_tracking_only()
                    if ok:
                        safe_notify("Removed status", type="positive")
                        return True
                    rollback_optimistic_tracking(state=page_state, snapshot=snapshot)
                    courses_list.refresh()
                    return False
                except Exception:
                    rollback_optimistic_tracking(state=page_state, snapshot=snapshot)
                    courses_list.refresh()
                    raise

            async def _create_submit(payload: dict[str, Any]) -> None:
                await api.post("/courses", payload)
                await _load()

            _open_create_dialog = build_share_course_dialog(
                username=username,
                parse_duration_hours=_parse_duration_hours,
                on_submit=_create_submit,
            )

            async def _save_edit(course_id: int, payload: dict[str, Any]) -> None:
                await api.put(f"/courses/{int(course_id)}", payload)
                await _load()

            def _render_edit_course_dialog(course: dict[str, Any]) -> None:
                open_edit_course_dialog(
                    course=course,
                    parse_duration_hours=_parse_duration_hours,
                    on_save=_save_edit,
                )

            async def _delete_course_and_reload(course_id: int) -> None:
                await api.delete(f"/courses/{int(course_id)}")
                await _load()

            async def _confirm_delete_course(course_id: int) -> None:
                await open_delete_course_dialog(
                    course_id=int(course_id),
                    on_delete=_delete_course_and_reload,
                )

            @guard_ui_action(title="Load course details failed")
            async def _open_details(course_id: int, *, focus_reviews: bool = False) -> None:
                await open_course_details_dialog(
                    api=api,
                    course_id=int(course_id),
                    focus_reviews=focus_reviews,
                    username=username,
                    is_admin=is_admin,
                    state=page_state,
                    normalize_course_view_mode=_normalize_course_view_mode,
                    format_review_summary=_format_review_summary,
                    format_short_date=_format_short_date,
                )

            @guard_ui_action(title="Recommend failed")
            async def _open_recommend_dialog(course_id: int) -> None:
                await open_recommend_course_dialog(
                    course_id=int(course_id),
                    username=username,
                    load_recommendations=lambda _cid: api.get(f"/courses/{int(_cid)}/recommendations"),
                    save_recommendation=lambda _cid, _note: api.post(
                        f"/courses/{int(_cid)}/recommendations",
                        {"note": str(_note or "").strip()},
                    ),
                    on_saved=_load,
                )

            @ui.refreshable
            def courses_list() -> None:
                normalized = normalize_courses_filter_values(
                    scope_value=str(scope_filter.value or "all"),
                    search_value=str(q.value or ""),
                    provider_value=str(provider_filter.value or ""),
                    category_value=str(category_filter.value or ""),
                    level_value=str(level_filter.value or ""),
                    status_value=str(status_filter.value or ""),
                    sort_value=str(sort_filter.value or ""),
                )
                shown = filter_courses(
                    courses=list(page_state.courses),
                    tracking_by_course_id=page_state.tracking_by_course_id,
                    scope_value=normalized.scope,
                    needle=normalized.search,
                    provider_value=normalized.provider,
                    category_value=normalized.category,
                    level_value=normalized.level,
                    status_value=normalized.status,
                )
                shown = sort_courses(
                    courses=shown,
                    sort_value=normalized.sort,
                    review_summary_by_course_id=page_state.review_summary_by_course_id,
                    parse_iso_datetime=_parse_iso_datetime,
                )

                with ui.column().classes("w-full gap-3"):
                    if ui_state.loading or not ui_state.loaded_once:
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
                        render_courses_empty_state(
                            scope_value=normalized.scope,
                            any_filters=bool(any_filters),
                            has_any_courses=bool(page_state.courses),
                            on_browse_all=lambda: setattr(scope_filter, "value", "all") or _refresh_list(),
                            on_share=lambda: _open_create_dialog(),
                            on_reset_all=_reset_all,
                            on_refresh=_load,
                        )
                        return

                    shown_total = len(shown)
                    shown_page = shown[: max(0, int(ui_state.visible_count))]

                    for c in shown_page:
                        course_id = int(c.get("id") or 0)
                        tracked = page_state.tracking_by_course_id.get(course_id)
                        can_edit = is_admin or (str(c.get("created_by") or "") == username)
                        url = str(c.get("url") or "").strip()
                        actions = build_course_card_actions(
                            course_id=course_id,
                            course_url=url,
                            course_row=c,
                            on_open_details=lambda _cid, _focus_reviews: _open_details(_cid, focus_reviews=_focus_reviews),
                            on_open_recommend=_open_recommend_dialog,
                            on_open_edit=_render_edit_course_dialog,
                            on_confirm_delete=_confirm_delete_course,
                        )

                        card_vm = map_course_card_view(
                            course_row=c,
                            tracked_row=tracked if isinstance(tracked, dict) else None,
                            review_summary_row=page_state.review_summary_by_course_id.get(course_id),
                            recommendation_summary_row=page_state.recommendation_summary_by_course_id.get(course_id),
                        )
                        render_course_card(
                            course_row=c,
                            tracked_row=tracked if isinstance(tracked, dict) else None,
                            card_vm=card_vm,
                            can_edit=can_edit,
                            has_url=bool(url),
                            actions=actions,
                            is_tracked_course=lambda _cid: int(_cid) in page_state.tracking_by_course_id,
                            resolve_status_value=resolve_tracking_status_value,
                            on_set_status=_set_tracking,
                            on_clear_status=_clear_tracking,
                        )

                    def _load_more() -> None:
                        ui_state.visible_count = compute_expanded_visible_count(
                            current_visible=int(ui_state.visible_count),
                            total_count=shown_total,
                            page_size=int(ui_state.page_size),
                        )
                        courses_list.refresh()

                    render_load_more_control(
                        shown_page_count=len(shown_page),
                        shown_total_count=shown_total,
                        on_load_more=_load_more,
                    )

            def _refresh_list(*_: Any) -> None:
                ui_state.visible_count = int(ui_state.page_size)
                _recompute_facet_options()
                active_filters.refresh()
                courses_list.refresh()

            def _clear_filter_values() -> None:
                reset = default_courses_filter_reset_state()
                scope_filter.value = reset.scope
                q.value = reset.search
                provider_filter.value = reset.provider
                category_filter.value = reset.category
                level_filter.value = reset.level
                status_filter.value = reset.status
                sort_filter.value = reset.sort
                scope_filter.update()
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

                chips = build_active_filter_chips(
                    scope_value=str(scope_filter.value or ""),
                    search_value=str(q.value or ""),
                    provider_value=str(provider_filter.value or ""),
                    category_value=str(category_filter.value or ""),
                    level_value=str(level_filter.value or ""),
                    status_value=str(status_filter.value or ""),
                    status_options={str(k): str(v) for k, v in dict(status_filter.options or {}).items()},
                )
                if not chips:
                    return

                def _clear_filter_key(key: str) -> None:
                    clear_map = {
                        "scope": lambda: setattr(scope_filter, "value", "all") or scope_filter.update(),
                        "search": lambda: setattr(q, "value", "") or q.update(),
                        "provider": lambda: setattr(provider_filter, "value", "") or provider_filter.update(),
                        "category": lambda: setattr(category_filter, "value", "") or category_filter.update(),
                        "level": lambda: setattr(level_filter, "value", "") or level_filter.update(),
                        "status": lambda: setattr(status_filter, "value", "") or status_filter.update(),
                    }
                    clear = clear_map.get(str(key))
                    if callable(clear):
                        clear()
                    active_filters.refresh()
                    courses_list.refresh()

                render_active_filter_chips(
                    chips=chips,
                    on_clear_key=_clear_filter_key,
                )

            def _render_rail() -> None:
                nonlocal provider_filter, category_filter, level_filter, status_filter, refresh_btn
                controls = render_filters_rail(
                    on_refresh=_load,
                    on_clear=_reset_all,
                    on_filters_changed=_refresh_list,
                )
                provider_filter = controls.provider_filter
                category_filter = controls.category_filter
                level_filter = controls.level_filter
                status_filter = controls.status_filter
                refresh_btn = controls.refresh_btn

            def _render_main() -> None:
                active_filters()
                courses_list()

            render_split_layout(rail=_render_rail, main=_render_main, rail_classes="lp-rail--bar")

            await _load()
            if route_init.initial_course_id > 0:
                await _open_details(route_init.initial_course_id, focus_reviews=route_init.initial_focus_reviews)
                if intent_matches_course(intent if isinstance(intent, dict) else None, route_init.initial_course_id):
                    app.storage.user.pop("courses_open_intent", None)
                if intent_matches_course(nav_intent if isinstance(nav_intent, dict) else None, route_init.initial_course_id):
                    pop_course_intent(username=username)
