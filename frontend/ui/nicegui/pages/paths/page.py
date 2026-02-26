"""Paths browse/admin page for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any, cast

from nicegui import app, ui

from frontend.ui.nicegui.components.catalog_hero import render_catalog_hero
from frontend.ui.nicegui.components.layout import render_catalog_scope, render_container, render_shell, render_split_layout
from frontend.ui.nicegui.components.loading import render_card_skeletons
from frontend.ui.nicegui.components.paths_sections import render_paths_filter_rail, render_paths_topbar
from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.core.errors import guard_ui_action, NotificationType, safe_notify
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.mutation_flow import run_optimistic_mutation
from frontend.ui.nicegui.core.navigation_intents import (
    pop_catalog_share_storage_intent,
)
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.paths.actions import (
    clear_path_filter_by_key,
    PathsFilterControls,
    resolve_paths_empty_state,
)
from frontend.ui.nicegui.pages.paths.controller import PathsPageController
from frontend.ui.nicegui.pages.paths.detail_flow import open_path_details_dialog
from frontend.ui.nicegui.pages.paths.dialogs import build_share_path_dialog
from frontend.ui.nicegui.pages.paths.filter_flow import (
    clear_paths_filters_and_refresh,
    recompute_paths_facet_options,
    refresh_paths_filter_list,
)
from frontend.ui.nicegui.pages.paths.orchestration import (
    load_all_paths,
    LoadAllPathsDeps,
    perform_create_path,
    perform_delete_path,
    run_select_path_flow,
    run_unselect_path_flow,
)
from frontend.ui.nicegui.pages.paths.reducers import (
    derive_paths_list_slice,
)
from frontend.ui.nicegui.pages.paths.route_init import resolve_paths_route_init
from frontend.ui.nicegui.pages.paths.sections import (
    PathsCardsRenderDeps,
    render_paths_active_filter_chips,
    render_paths_cards_block,
    render_paths_collection_intro,
    render_paths_empty_state,
)
from frontend.ui.nicegui.pages.paths.state import PathsPageState, PathsPageUiState
from frontend.ui.nicegui.pages.paths.transitions import (
    apply_optimistic_select,
    apply_optimistic_unselect,
    rollback_optimistic_selection,
)
from frontend.ui.nicegui.pages.paths.ui_glue import (
    collect_active_filter_chips,
    compute_paths_meta_text,
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
    """Register the paths routes."""

    @ui.page("/manage/paths")
    async def paths_page() -> None:
        user = await require_user(store, api)
        if user is None:
            return
        request = getattr(ui.context.client, "request", None)
        share_intent = pop_catalog_share_storage_intent(storage_user=app.storage.user)
        render_shell(title="Paths", store=store, api=api)
        username = str(user.get("username") or "")
        is_admin = str(user.get("role") or "") == "admin"
        controller = PathsPageController(api=api)
        controller_state = PathsPageState()
        ui_state = PathsPageUiState()

        def _notify(message: str, kind: str) -> None:
            normalized = str(kind or "").strip().lower()
            if normalized not in {"positive", "negative", "warning", "info", "ongoing"}:
                normalized = "info"
            safe_notify(message, type=cast(NotificationType, normalized))

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
                def _on_scope_selected() -> None:
                    if scope_filter is not None:
                        scope_filter.value = "selected"
                        scope_filter.update()

                return await run_select_path_flow(
                    path_id=int(path_id),
                    controller=controller,
                    state=controller_state,
                    reload_selected=_reload_selected,
                    ensure_selected_detail=_ensure_selected_detail,
                    reload_tracking=_reload_tracking,
                    on_scope_selected=_on_scope_selected,
                    notify=_notify,
                    refresh_paths_list_ui=_refresh_paths_list,
                    open_details=_open_details,
                )

            return await run_optimistic_mutation(
                apply_optimistic=lambda: apply_optimistic_select(state=controller_state, path_id=int(path_id)),
                perform_mutation=_perform_select,
                rollback=lambda snapshot: rollback_optimistic_selection(state=controller_state, snapshot=snapshot),
                refresh_ui=_refresh_paths_list,
            )

        @guard_ui_action(title="Unselect failed")
        async def _unselect(path_id: int) -> bool:
            async def _perform_unselect() -> bool:
                return await run_unselect_path_flow(
                    path_id=int(path_id),
                    controller=controller,
                    state=controller_state,
                    reload_selected=_reload_selected,
                    notify=_notify,
                    refresh_paths_list_ui=_refresh_paths_list,
                )

            return await run_optimistic_mutation(
                apply_optimistic=lambda: apply_optimistic_unselect(state=controller_state, path_id=int(path_id)),
                perform_mutation=_perform_unselect,
                rollback=lambda snapshot: rollback_optimistic_selection(state=controller_state, snapshot=snapshot),
                refresh_ui=_refresh_paths_list,
            )

        @guard_ui_action(title="Delete path failed")
        async def _delete_path(path_id: int) -> None:
            await perform_delete_path(
                path_id=int(path_id),
                controller=controller,
                reload_page=_load_all,
            )
            safe_notify("Path deleted", type="positive")

        @guard_ui_action(title="Load path details failed")
        async def _open_details(path_id: int, *, view_mode: str = "full") -> None:
            """Open a path dialog."""
            await open_path_details_dialog(
                path_id=int(path_id),
                view_mode=view_mode,
                controller=controller,
                state=controller_state,
                username=username,
                is_admin=is_admin,
                on_paths_refresh=paths_list.refresh,
            )

        with render_catalog_scope(variant="paths").classes("lp-container"):
            status_filter: Any = None
            refresh_btn: Any = None
            sort_filter: Any = None
            scope_filter: Any = None

            _, create_course_ids, _open_create_dialog = build_share_path_dialog(
                username=username,
                on_submit=lambda payload: perform_create_path(
                    payload=payload,
                    controller=controller,
                    reload_page=_load_all,
                ),
            )

            # Top bar (search + primary action + sort + count).
            open_share_from_intent = str(share_intent or "") == "path"
            route_init = resolve_paths_route_init(request=request)

            q, scope_filter, sort_filter, meta = render_paths_topbar(
                initial_scope=route_init.initial_scope,
                on_open_create_dialog=_open_create_dialog,
            )
            controls = PathsFilterControls(
                scope_filter=scope_filter,
                search_input=q,
                status_filter=status_filter,
                sort_filter=sort_filter,
            )

            def _recompute_facet_options() -> None:
                recompute_paths_facet_options(
                    controls=PathsFilterControls(
                        scope_filter=scope_filter,
                        search_input=q,
                        status_filter=status_filter,
                        sort_filter=sort_filter,
                    ),
                    state=controller_state,
                )

            def _refresh_list(*_: Any) -> None:
                refresh_paths_filter_list(
                    ui_state=ui_state,
                    recompute_facet_options=_recompute_facet_options,
                    refresh_active_filters=_refresh_active_filters,
                    refresh_paths_list_ui=_refresh_paths_list,
                )

            def _clear_filter_values() -> None:
                clear_paths_filters_and_refresh(
                    controls=controls,
                    recompute_facet_options=_recompute_facet_options,
                    refresh_active_filters=_refresh_active_filters,
                    refresh_paths_list_ui=_refresh_paths_list,
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
                chips = collect_active_filter_chips(
                    scope_value=str(scope_filter.value or ""),
                    search_value=str(q.value or ""),
                    status_value=str(status_filter.value or "") if status_filter is not None else "",
                    sort_value=str(sort_filter.value or ""),
                    status_options=dict(status_filter.options or {}) if status_filter is not None else {},
                    sort_options=dict(sort_filter.options or {}),
                )

                def _on_clear_key(key: str) -> None:
                    clear_path_filter_by_key(
                        key=str(key),
                        controls=PathsFilterControls(
                            scope_filter=scope_filter,
                            search_input=q,
                            status_filter=status_filter,
                            sort_filter=sort_filter,
                        ),
                    )
                    _refresh_list()

                render_paths_active_filter_chips(
                    chips=chips,
                    on_clear_key=_on_clear_key,
                )

            @ui.refreshable
            def paths_list() -> None:
                list_slice = derive_paths_list_slice(
                    paths=controller_state.paths,
                    selected_by_id=controller_state.selected_by_id,
                    path_review_summary_by_id=controller_state.path_review_summary_by_id,
                    scope_value=str(scope_filter.value or "all"),
                    search_value=str(q.value or ""),
                    status_value=str(status_filter.value or "").strip(),
                    sort_value=str(sort_filter.value or "").strip(),
                    path_matches_state=_path_matches_state,
                    parse_iso_datetime=parse_iso_datetime,
                )
                normalized = list_slice.normalized
                shown = list_slice.shown

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

                    def _browse_all() -> None:
                        scope_filter.value = "all"
                        _refresh_list()

                    if render_paths_empty_state(
                        empty_state=empty_state,
                        on_browse_all=_browse_all,
                        on_refresh=_load_all,
                        on_share=_open_create_dialog,
                        on_browse_courses=lambda: ui.navigate.to("/explore?tab=courses"),
                        on_reset_all=_reset_all,
                    ):
                        return

                    render_paths_collection_intro()
                    render_paths_cards_block(
                        shown=shown,
                        deps=PathsCardsRenderDeps(
                            username=username,
                            is_admin=is_admin,
                            controller=controller,
                            controller_state=controller_state,
                            ui_state=ui_state,
                            refresh_paths_list_ui=_refresh_paths_list,
                            recompute_facet_options=_recompute_facet_options,
                            open_details=lambda _pid, _mode: _open_details(_pid, view_mode=_mode),
                            select_path=_select,
                            unselect_path=_unselect,
                            delete_path=_delete_path,
                            load_all=_load_all,
                        ),
                    )

            async def _load_all() -> None:
                """Reload all data for this page."""
                await load_all_paths(
                    ui_state=ui_state,
                    controller_state=controller_state,
                    deps=LoadAllPathsDeps(
                        controller=controller,
                        refresh_btn=refresh_btn,
                        meta=meta,
                        create_course_ids=create_course_ids,
                        compute_course_options=_course_options,
                        recompute_facet_options=_recompute_facet_options,
                        refresh_paths_list_ui=_refresh_paths_list,
                        notify_error=lambda message: safe_notify(message, type="negative"),
                        compute_meta_text=lambda path_count: compute_paths_meta_text(path_count=path_count),
                    ),
                )

            def _refresh_active_filters() -> None:
                active_filters.refresh()

            def _refresh_paths_list() -> None:
                paths_list.refresh()

            def _render_rail() -> None:
                nonlocal status_filter, refresh_btn
                status_filter, refresh_btn = render_paths_filter_rail(
                    on_refresh=_load_all,
                    on_reset=_reset_all,
                    on_status_change=_refresh_list,
                )

            def _render_main() -> None:
                render_catalog_hero(
                    eyebrow="Roadmap mode",
                    title="Follow structured learning paths",
                    subtitle="Move milestone by milestone and keep long-term goals visible.",
                )
                active_filters()
                paths_list()

            render_split_layout(rail=_render_rail, main=_render_main, rail_classes="lp-rail--bar")

            await _load_all()
            if open_share_from_intent:
                _open_create_dialog()
