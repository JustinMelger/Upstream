"""Courses browse/admin page for the NiceGUI frontend."""

from __future__ import annotations

from datetime import timezone
from functools import partial
from typing import Any

from nicegui import app, ui

from frontend.ui.nicegui.components.layout import render_container, render_shell, render_split_layout
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.mutation_flow import run_optimistic_mutation
from frontend.ui.nicegui.core.navigation_intents import (
    get_course_intent,
    get_course_storage_intent,
    pop_course_intent,
    pop_course_storage_intent,
)
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.courses.actions import (
    build_course_card_actions,
    clear_course_filter_by_key,
    CoursesFilterControls,
    recompute_course_facet_controls,
)
from frontend.ui.nicegui.pages.courses.controller import CoursesPageController
from frontend.ui.nicegui.pages.courses.detail_flow import open_course_details_flow
from frontend.ui.nicegui.pages.courses.dialogs import (
    build_share_course_dialog,
    open_delete_course_dialog,
    open_edit_course_dialog,
    open_recommend_course_dialog,
)
from frontend.ui.nicegui.pages.courses.filters import normalize_courses_filter_values
from frontend.ui.nicegui.pages.courses.orchestration import (
    clear_course_filter_values,
    load_courses,
    open_delete_course_confirmation,
    perform_clear_tracking,
    perform_create_course,
    perform_delete_course_from_dialog,
    perform_set_tracking,
    perform_update_course,
    refresh_course_recommendation_summary,
    refresh_courses_list,
    reload_tracking_only,
)
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
    render_courses_topbar,
    render_filters_rail,
    render_load_more_control,
)
from frontend.ui.nicegui.pages.courses.state import CoursesPageState, CoursesPageUiState
from frontend.ui.nicegui.pages.courses.transitions import (
    apply_optimistic_tracking_clear,
    apply_optimistic_tracking_set,
    rollback_optimistic_tracking,
)
from frontend.ui.nicegui.pages.courses.ui_glue import (
    build_active_filter_chips,
    compute_courses_meta_text,
    compute_expanded_visible_count,
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
            intent = get_course_storage_intent(storage_user=app.storage.user)
            nav_intent = get_course_intent(username=username)
            route_init = resolve_courses_route_init(
                request=request,
                storage_intent=intent if isinstance(intent, dict) else None,
                nav_intent=nav_intent if isinstance(nav_intent, dict) else None,
            )

            topbar = render_courses_topbar(
                initial_scope=route_init.initial_scope,
                on_share=lambda: _open_create_dialog(),
            )
            q = topbar.search_input
            scope_filter = topbar.scope_filter
            sort_filter = topbar.sort_filter
            meta = topbar.meta
            # Late-bind to avoid "defined later" ordering issues.
            sort_filter.on("update:model-value", lambda *_: _refresh_list())
            scope_filter.on("update:model-value", lambda *_: _refresh_list())

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
                normalized = normalize_courses_filter_values(
                    scope_value=str(scope_filter.value or "all"),
                    search_value=str(q.value or ""),
                    provider_value=str(provider_filter.value or ""),
                    category_value=str(category_filter.value or ""),
                    level_value=str(level_filter.value or ""),
                    status_value=str(status_filter.value or ""),
                    sort_value=str(sort_filter.value or ""),
                )
                recompute_course_facet_controls(
                    controls=CoursesFilterControls(
                        scope_filter=scope_filter,
                        search_input=q,
                        provider_filter=provider_filter,
                        category_filter=category_filter,
                        level_filter=level_filter,
                        status_filter=status_filter,
                        sort_filter=sort_filter,
                    ),
                    courses=page_state.courses,
                    tracking_by_course_id=page_state.tracking_by_course_id,
                    normalized_filters=normalized,
                    compute_facet_counts=compute_facet_counts,
                    build_count_options=build_count_options,
                    build_status_options=_build_status_options,
                )

            async def _load() -> None:
                await load_courses(
                    ui_state=ui_state,
                    page_state=page_state,
                    controller=controller,
                    controls=CoursesFilterControls(
                        scope_filter=scope_filter,
                        search_input=q,
                        provider_filter=provider_filter,
                        category_filter=category_filter,
                        level_filter=level_filter,
                        status_filter=status_filter,
                        sort_filter=sort_filter,
                    ),
                    refresh_btn=refresh_btn,
                    meta=meta,
                    recompute_facet_options=_recompute_facet_options,
                    refresh_courses_list_ui=courses_list.refresh,
                    notify_error=lambda message: safe_notify(message, type="negative"),
                    compute_meta_text=compute_courses_meta_text,
                )

            async def _reload_tracking_only() -> bool:
                return await reload_tracking_only(
                    page_state=page_state,
                    controller=controller,
                    recompute_facet_options=_recompute_facet_options,
                    refresh_courses_list_ui=courses_list.refresh,
                    notify_error=lambda message: safe_notify(message, type="negative"),
                )

            @guard_ui_action(title="Update status failed")
            async def _set_tracking(course_id: int, status: str) -> bool:
                return await run_optimistic_mutation(
                    apply_optimistic=lambda: apply_optimistic_tracking_set(
                        state=page_state,
                        course_id=int(course_id),
                        status=str(status),
                    ),
                    perform_mutation=lambda: perform_set_tracking(
                        course_id=int(course_id),
                        status=str(status),
                        controller=controller,
                        page_state=page_state,
                        recompute_facet_options=_recompute_facet_options,
                        refresh_courses_list_ui=courses_list.refresh,
                        notify_error=lambda message: safe_notify(message, type="negative"),
                    ),
                    rollback=lambda snapshot: rollback_optimistic_tracking(state=page_state, snapshot=snapshot),
                    refresh_ui=courses_list.refresh,
                    on_success=lambda: safe_notify("Updated status", type="positive"),
                )

            @guard_ui_action(title="Remove status failed")
            async def _clear_tracking(course_id: int) -> bool:
                return await run_optimistic_mutation(
                    apply_optimistic=lambda: apply_optimistic_tracking_clear(state=page_state, course_id=int(course_id)),
                    perform_mutation=lambda: perform_clear_tracking(
                        course_id=int(course_id),
                        controller=controller,
                        page_state=page_state,
                        recompute_facet_options=_recompute_facet_options,
                        refresh_courses_list_ui=courses_list.refresh,
                        notify_error=lambda message: safe_notify(message, type="negative"),
                    ),
                    rollback=lambda snapshot: rollback_optimistic_tracking(state=page_state, snapshot=snapshot),
                    refresh_ui=courses_list.refresh,
                    on_success=lambda: safe_notify("Removed status", type="positive"),
                )

            _open_create_dialog = build_share_course_dialog(
                username=username,
                parse_duration_hours=_parse_duration_hours,
                on_submit=lambda payload: perform_create_course(
                    payload=payload,
                    controller=controller,
                    reload_page=_load,
                ),
            )

            @guard_ui_action(title="Load course details failed")
            async def _open_details(course_id: int, *, focus_reviews: bool = False) -> None:
                await open_course_details_flow(
                    course_id=int(course_id),
                    focus_reviews=focus_reviews,
                    username=username,
                    is_admin=is_admin,
                    state=page_state,
                    controller=controller,
                    normalize_course_view_mode=_normalize_course_view_mode,
                    format_short_date=_format_short_date,
                )

            @guard_ui_action(title="Recommend failed")
            async def _open_recommend_dialog(course_id: int) -> None:
                await open_recommend_course_dialog(
                    course_id=int(course_id),
                    username=username,
                    load_recommendations=lambda _cid: controller.load_course_recommendations(course_id=int(_cid)),
                    save_recommendation=lambda _cid, _note: controller.save_course_recommendation(
                        course_id=int(_cid),
                        note=str(_note or ""),
                    ),
                    on_saved=partial(
                        refresh_course_recommendation_summary,
                        course_id=int(course_id),
                        username=username,
                        controller=controller,
                        page_state=page_state,
                        refresh_courses_list_ui=courses_list.refresh,
                    ),
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
                            on_open_edit=lambda course: open_edit_course_dialog(
                                course=course,
                                parse_duration_hours=_parse_duration_hours,
                                on_save=partial(
                                    perform_update_course,
                                    controller=controller,
                                    reload_page=_load,
                                ),
                            ),
                            on_confirm_delete=partial(
                                open_delete_course_confirmation,
                                open_delete_dialog=open_delete_course_dialog,
                                on_delete_course=partial(
                                    perform_delete_course_from_dialog,
                                    controller=controller,
                                    reload_page=_load,
                                ),
                            ),
                        )

                        card_vm = map_course_card_view(
                            course_row=c,
                            tracked_row=tracked if isinstance(tracked, dict) else None,
                            review_summary_row=page_state.review_summary_by_course_id.get(course_id),
                            recommendation_summary_row=page_state.recommendation_summary_by_course_id.get(course_id),
                        )
                        is_preview_open = int(ui_state.preview_course_id or 0) == int(course_id)
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
                            has_video_preview=bool(card_vm.has_video_preview),
                            is_preview_open=bool(is_preview_open),
                            preview_embed_url=str(card_vm.video_embed_url or ""),
                            on_toggle_preview=lambda _cid=course_id: (
                                setattr(
                                    ui_state,
                                    "preview_course_id",
                                    None if int(ui_state.preview_course_id or 0) == int(_cid) else int(_cid),
                                ),
                                courses_list.refresh(),
                            ),
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
                refresh_courses_list(
                    ui_state=ui_state,
                    recompute_facet_options=_recompute_facet_options,
                    refresh_active_filters=active_filters.refresh,
                    refresh_courses_list_ui=courses_list.refresh,
                )

            def _clear_filter_values() -> None:
                clear_course_filter_values(
                    controls=CoursesFilterControls(
                        scope_filter=scope_filter,
                        search_input=q,
                        provider_filter=provider_filter,
                        category_filter=category_filter,
                        level_filter=level_filter,
                        status_filter=status_filter,
                        sort_filter=sort_filter,
                    ),
                    refresh_active_filters=active_filters.refresh,
                    refresh_courses_list_ui=courses_list.refresh,
                )

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
                    clear_course_filter_by_key(
                        key=str(key),
                        controls=CoursesFilterControls(
                            scope_filter=scope_filter,
                            search_input=q,
                            provider_filter=provider_filter,
                            category_filter=category_filter,
                            level_filter=level_filter,
                            status_filter=status_filter,
                            sort_filter=sort_filter,
                        ),
                    )
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
                    pop_course_storage_intent(storage_user=app.storage.user)
                if intent_matches_course(nav_intent if isinstance(nav_intent, dict) else None, route_init.initial_course_id):
                    pop_course_intent(username=username)
