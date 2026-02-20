"""Paths browse/admin page for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any

from nicegui import app, ui

from frontend.ui.nicegui.components.layout import render_container, render_shell, render_split_layout
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.pagination import render_load_more_footer
from frontend.ui.nicegui.components.path_card import render_path_card
from frontend.ui.nicegui.components.paths_sections import render_paths_filter_rail, render_paths_topbar
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.mutation_flow import run_optimistic_mutation
from frontend.ui.nicegui.core.navigation_intents import (
    get_path_intent,
    get_path_storage_intent,
    pop_path_intent,
    pop_path_storage_intent,
)
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.paths.actions import (
    build_path_card_actions,
    clear_path_filter_by_key,
    PathsFilterControls,
    recompute_path_status_filter,
    resolve_paths_empty_state,
)
from frontend.ui.nicegui.pages.paths.controller import PathsPageController
from frontend.ui.nicegui.pages.paths.detail_flow import open_path_details_dialog
from frontend.ui.nicegui.pages.paths.dialogs import build_share_path_dialog, open_edit_path_dialog
from frontend.ui.nicegui.pages.paths.filters import normalize_paths_filter_values
from frontend.ui.nicegui.pages.paths.orchestration import (
    clear_path_filter_values,
    load_all_paths,
    refresh_paths_list,
)
from frontend.ui.nicegui.pages.paths.reducers import (
    apply_scope_and_status,
    build_status_options,
    compute_status_counts,
    filter_paths_by_needle,
    sort_paths,
)
from frontend.ui.nicegui.pages.paths.route_init import intent_matches_path, resolve_paths_route_init
from frontend.ui.nicegui.pages.paths.state import PathsPageState, PathsPageUiState
from frontend.ui.nicegui.pages.paths.transitions import (
    apply_optimistic_select,
    apply_optimistic_unselect,
    rollback_optimistic_selection,
)
from frontend.ui.nicegui.pages.paths.ui_glue import (
    collect_active_filter_chips,
    compute_expanded_visible_count,
    compute_paths_meta_text,
)
from frontend.ui.nicegui.pages.paths.view_model import (
    map_path_card_view,
)


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
        ui_state = PathsPageUiState()

        async def _reload_selected() -> bool:
            """Reload selected path rows (used after select/unselect/status updates)."""
            try:
                await controller.reload_selected(state=controller_state)
                return True
            except ApiError as exc:
                safe_notify(str(exc), type="negative")
                return False

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
        async def _select(path_id: int) -> bool:
            async def _perform_select() -> bool:
                seeded, detail = await controller.select_path(path_id=int(path_id), state=controller_state)
                reloaded = await _reload_selected()
                if not reloaded:
                    safe_notify("Path selected, but selected list failed to refresh", type="warning")
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
                safe_notify(msg, type="positive")
                paths_list.refresh()
                await _open_details(path_id)
                return True

            return await run_optimistic_mutation(
                apply_optimistic=lambda: apply_optimistic_select(state=controller_state, path_id=int(path_id)),
                perform_mutation=_perform_select,
                rollback=lambda snapshot: rollback_optimistic_selection(state=controller_state, snapshot=snapshot),
                refresh_ui=paths_list.refresh,
            )

        @guard_ui_action(title="Unselect failed")
        async def _unselect(path_id: int) -> bool:
            async def _perform_unselect() -> bool:
                await controller.unselect_path(path_id=int(path_id))
                reloaded = await _reload_selected()
                if not reloaded:
                    safe_notify("Path untracked, but selected list failed to refresh", type="warning")
                controller_state.selected_detail_by_path_id.pop(int(path_id), None)
                paths_list.refresh()
                return True

            return await run_optimistic_mutation(
                apply_optimistic=lambda: apply_optimistic_unselect(state=controller_state, path_id=int(path_id)),
                perform_mutation=_perform_unselect,
                rollback=lambda snapshot: rollback_optimistic_selection(state=controller_state, snapshot=snapshot),
                refresh_ui=paths_list.refresh,
            )

        @guard_ui_action(title="Delete path failed")
        async def _delete_path(path_id: int) -> None:
            await controller.delete_path(path_id=int(path_id))
            await _load_all()
            safe_notify("Path deleted", type="positive")

        async def _refresh_path_recommendation_summary(path_id: int) -> None:
            row = await controller.load_recommendation_summary_for_path(path_id=int(path_id))
            if isinstance(row, dict):
                controller_state.path_recommendation_summary_by_id[int(path_id)] = row
            else:
                controller_state.path_recommendation_summary_by_id.pop(int(path_id), None)
            paths_list.refresh()

        async def _open_edit(*, path_id: int, detail: dict[str, Any], detail_dialog: ui.dialog | None) -> None:
            """Open an edit dialog for a path (owner/admin only, enforced by backend)."""

            async def _save_edit(payload: dict[str, Any]) -> None:
                await controller.update_path(path_id=int(path_id), payload=payload)
                await _load_all()
                paths_list.refresh()

            await open_edit_path_dialog(
                detail=detail,
                course_by_id=controller_state.course_by_id,
                detail_dialog=detail_dialog,
                on_save=_save_edit,
            )

        @guard_ui_action(title="Load path details failed")
        async def _open_details(path_id: int, *, view_mode: str = "full") -> None:
            """Open a path dialog.

            Args:
                path_id: Path ID.
                view_mode: Either "full" or "reviews".
            """
            await open_path_details_dialog(
                path_id=int(path_id),
                view_mode=view_mode,
                controller=controller,
                state=controller_state,
                username=username,
                is_admin=is_admin,
                on_paths_refresh=paths_list.refresh,
            )

        with render_container():
            # Rail filters.
            status_filter: Any = None
            refresh_btn: Any = None
            sort_filter: Any = None
            scope_filter: Any = None

            # Share/create dialog (pre-built so opening is instant).
            async def _create_submit(payload: dict[str, Any]) -> None:
                await controller.create_path(payload=payload)
                await _load_all()

            _, create_course_ids, _open_create_dialog = build_share_path_dialog(
                username=username,
                on_submit=_create_submit,
            )

            # Top bar (search + primary action + sort + count).
            request = getattr(ui.context.client, "request", None)
            intent = get_path_storage_intent(storage_user=app.storage.user)
            nav_intent = get_path_intent(username=username)
            route_init = resolve_paths_route_init(
                request=request,
                storage_intent=intent if isinstance(intent, dict) else None,
                nav_intent=nav_intent if isinstance(nav_intent, dict) else None,
                normalize_view_mode=_normalize_path_view_mode,
            )

            q, scope_filter, sort_filter, meta = render_paths_topbar(
                initial_scope=route_init.initial_scope,
                on_open_create_dialog=_open_create_dialog,
            )

            def _recompute_facet_options() -> None:
                """Recompute status facet options with counts based on the current local filters."""
                normalized = normalize_paths_filter_values(
                    scope_value=str(scope_filter.value or "all"),
                    search_value=str(q.value or ""),
                    status_value=str(status_filter.value or ""),
                    sort_value=str(sort_filter.value or ""),
                )
                recompute_path_status_filter(
                    controls=PathsFilterControls(
                        scope_filter=scope_filter,
                        search_input=q,
                        status_filter=status_filter,
                        sort_filter=sort_filter,
                    ),
                    paths=controller_state.paths,
                    selected_by_id=controller_state.selected_by_id,
                    normalized_filters=normalized,
                    compute_status_counts=compute_status_counts,
                    build_status_options=build_status_options,
                )

            def _refresh_list(*_: Any) -> None:
                refresh_paths_list(
                    ui_state=ui_state,
                    recompute_facet_options=_recompute_facet_options,
                    refresh_active_filters=active_filters.refresh,
                    refresh_paths_list_ui=paths_list.refresh,
                )

            def _clear_filter_values() -> None:
                clear_path_filter_values(
                    controls=PathsFilterControls(
                        scope_filter=scope_filter,
                        search_input=q,
                        status_filter=status_filter,
                        sort_filter=sort_filter,
                    ),
                    recompute_facet_options=_recompute_facet_options,
                    refresh_active_filters=active_filters.refresh,
                    refresh_paths_list_ui=paths_list.refresh,
                )

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

                chips = collect_active_filter_chips(
                    scope_value=str(scope_filter.value or ""),
                    search_value=str(q.value or ""),
                    status_value=str(status_filter.value or "") if status_filter is not None else "",
                    sort_value=str(sort_filter.value or ""),
                    status_options=dict(status_filter.options or {}) if status_filter is not None else {},
                    sort_options=dict(sort_filter.options or {}),
                )

                if not chips:
                    return

                with ui.row().classes("items-center gap-2 w-full"):
                    for chip in chips:
                        _chip(
                            chip.label,
                            lambda key=chip.key: (
                                clear_path_filter_by_key(
                                    key=key,
                                    controls=PathsFilterControls(
                                        scope_filter=scope_filter,
                                        search_input=q,
                                        status_filter=status_filter,
                                        sort_filter=sort_filter,
                                    ),
                                )
                                and _refresh_list()
                            ),
                        )

            @ui.refreshable
            def paths_list() -> None:
                normalized = normalize_paths_filter_values(
                    scope_value=str(scope_filter.value or "all"),
                    search_value=str(q.value or ""),
                    status_value=str(status_filter.value or "").strip(),
                    sort_value=str(sort_filter.value or "").strip(),
                )
                shown = filter_paths_by_needle(controller_state.paths, normalized.search)
                shown = apply_scope_and_status(
                    paths=shown,
                    selected_by_id=controller_state.selected_by_id,
                    scope_value=normalized.scope,
                    status_value=normalized.status,
                    path_matches_state=_path_matches_state,
                )
                shown = sort_paths(
                    paths=shown,
                    sort_value=normalized.sort,
                    path_review_summary_by_id=controller_state.path_review_summary_by_id,
                    parse_iso_datetime=parse_iso_datetime,
                )

                with ui.column().classes("w-full gap-3"):
                    if ui_state.loading or not ui_state.loaded_once:
                        render_card_skeletons(count=4)
                        return

                    any_filters = any([str(q.value or "").strip(), str(status_filter.value or "").strip()])
                    empty_state = resolve_paths_empty_state(
                        has_rows=bool(shown),
                        scope_value=normalized.scope,
                        has_any_filters=bool(any_filters),
                        has_any_paths=bool(controller_state.paths),
                    )
                    if empty_state != "has_rows":
                        if empty_state == "selected_empty":
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
                        if empty_state == "catalog_empty":
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
                    shown_page = shown[: max(0, int(ui_state.visible_count))]
                    for p in shown_page:
                        pid = int(p.get("id") or 0)
                        selected = controller_state.selected_by_id.get(pid)
                        can_edit = is_admin or (str(p.get("created_by") or "") == username)
                        is_tracked = selected is not None
                        detail = controller_state.selected_detail_by_path_id.get(pid) if selected else None
                        card_vm = map_path_card_view(
                            path_row=p,
                            is_tracked=is_tracked,
                            detail=detail if isinstance(detail, dict) else None,
                            tracking_by_course_id=controller_state.tracking_by_course_id,
                            review_summary_row=controller_state.path_review_summary_by_id.get(pid),
                            recommendation_summary_row=controller_state.path_recommendation_summary_by_id.get(pid),
                        )

                        actions = build_path_card_actions(
                            path_id=pid,
                            is_tracked=selected is not None,
                            username=username,
                            get_user_note=lambda _path_id, _username: controller.get_user_recommendation_note(
                                path_id=int(_path_id),
                                username=str(_username),
                            ),
                            save_recommendation=lambda _path_id, _note: controller.save_recommendation(
                                path_id=int(_path_id),
                                note=str(_note),
                            ),
                            on_saved=lambda _pid=pid: _refresh_path_recommendation_summary(_pid),
                            get_path_detail=lambda _pid: controller.get_path_detail(path_id=int(_pid)),
                            on_open_edit=lambda _pid, _detail: _open_edit(path_id=_pid, detail=_detail, detail_dialog=None),
                            on_delete=_delete_path,
                            on_open_details=lambda _pid, _mode: _open_details(_pid, view_mode=_mode),
                            on_select=_select,
                            on_unselect=_unselect,
                            on_after_toggle=_recompute_facet_options,
                        )

                        render_path_card(
                            path_row=p,
                            card_class_suffix=card_vm.card_class_suffix,
                            is_new=card_vm.is_new,
                            is_updated=card_vm.is_updated,
                            rating_badge=card_vm.rating_badge,
                            recommendation_badge=card_vm.recommendation_badge,
                            can_edit=can_edit,
                            shared_by=card_vm.shared_by,
                            tracking_label_text=card_vm.tracking_label_text,
                            tracking_chip_cls=card_vm.tracking_chip_cls,
                            completed=card_vm.completed,
                            total_courses=card_vm.total_courses,
                            progress=card_vm.progress,
                            milestone=card_vm.milestone,
                            milestone_class=card_vm.milestone_class,
                            impact=card_vm.impact,
                            next_title=card_vm.next_title,
                            on_review=actions.on_review,
                            on_recommend=actions.on_recommend,
                            on_copy_link=actions.on_copy_link,
                            on_edit=actions.on_edit,
                            on_delete=actions.on_delete,
                            on_view=actions.on_view,
                            on_track_toggle=actions.on_track_toggle,
                            track_toggle_label=actions.track_toggle_label,
                        )

                    if total > len(shown_page):

                        def _load_more() -> None:
                            ui_state.visible_count = compute_expanded_visible_count(
                                current_visible=int(ui_state.visible_count),
                                total_count=int(total),
                                page_size=int(ui_state.page_size),
                            )
                            paths_list.refresh()

                        render_load_more_footer(
                            shown_page_count=len(shown_page),
                            shown_total_count=total,
                            on_load_more=_load_more,
                        )

            async def _load_all() -> None:
                """Reload all data for this page."""
                await load_all_paths(
                    ui_state=ui_state,
                    controller_state=controller_state,
                    controller=controller,
                    refresh_btn=refresh_btn,
                    meta=meta,
                    create_course_ids=create_course_ids,
                    compute_course_options=_course_options,
                    recompute_facet_options=_recompute_facet_options,
                    refresh_paths_list_ui=paths_list.refresh,
                    notify_error=lambda message: safe_notify(message, type="negative"),
                    compute_meta_text=lambda path_count: compute_paths_meta_text(path_count=path_count),
                )

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
            if route_init.initial_path_id > 0:
                await _open_details(route_init.initial_path_id, view_mode=route_init.initial_dialog_mode)
                if intent_matches_path(intent if isinstance(intent, dict) else None, route_init.initial_path_id):
                    pop_path_storage_intent(storage_user=app.storage.user)
                if intent_matches_path(nav_intent if isinstance(nav_intent, dict) else None, route_init.initial_path_id):
                    pop_path_intent(username=username)
