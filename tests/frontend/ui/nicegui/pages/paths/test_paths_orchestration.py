from __future__ import annotations

from dataclasses import dataclass

import pytest

from frontend.ui.nicegui.domains.paths.actions import PathsFilterControls
from frontend.ui.nicegui.domains.paths.orchestration import (
    clear_path_filter_values,
    PathsListRefreshDeps,
    perform_create_path,
    perform_delete_path,
    perform_update_path,
    refresh_paths_list,
    run_select_path_flow,
    run_unselect_path_flow,
)
from frontend.ui.nicegui.domains.paths.state import PathsPageState, PathsPageUiState


@dataclass(slots=True)
class _Controller:
    seeded: int = 0
    detail: dict | None = None

    async def select_path(self, *, path_id: int, state: PathsPageState) -> tuple[int, dict | None]:
        return self.seeded, self.detail

    async def unselect_path(self, *, path_id: int) -> bool:
        return True

    async def create_path(self, *, payload: dict) -> dict:
        return payload

    async def update_path(self, *, path_id: int, payload: dict) -> dict:
        return payload

    async def delete_path(self, *, path_id: int) -> bool:
        return True


@dataclass(slots=True)
class _Control:
    value: str = ""
    updated: int = 0

    def update(self) -> None:
        self.updated += 1


@pytest.mark.unit
@pytest.mark.anyio
async def test_run_select_path_flow_sets_scope_and_notifies_success() -> None:
    state = PathsPageState()
    controller = _Controller(seeded=2, detail={"id": 7})
    calls: list[str] = []
    notifications: list[tuple[str, str]] = []

    async def _reload_selected() -> bool:
        calls.append("reload_selected")
        return True

    async def _ensure_selected_detail(path_id: int) -> None:
        calls.append(f"ensure:{path_id}")

    async def _reload_tracking() -> None:
        calls.append("reload_tracking")

    def _on_scope_selected() -> None:
        calls.append("scope_selected")

    def _notify(message: str, kind: str) -> None:
        notifications.append((message, kind))

    def _refresh() -> None:
        calls.append("refresh")

    async def _open_details(path_id: int) -> None:
        calls.append(f"open:{path_id}")

    ok = await run_select_path_flow(
        path_id=7,
        controller=controller,  # type: ignore[arg-type]
        state=state,
        reload_selected=_reload_selected,
        ensure_selected_detail=_ensure_selected_detail,
        reload_tracking=_reload_tracking,
        on_scope_selected=_on_scope_selected,
        notify=_notify,
        refresh_paths_list_ui=_refresh,
        open_details=_open_details,
    )

    assert ok is True
    assert state.selected_detail_by_path_id[7]["id"] == 7
    assert "reload_tracking" in calls
    assert "scope_selected" in calls
    assert ("Path added to My learning · 2 course(s) set to Interested", "positive") in notifications
    assert "open:7" in calls


@pytest.mark.unit
@pytest.mark.anyio
async def test_run_select_path_flow_warns_when_selected_reload_fails() -> None:
    state = PathsPageState()
    controller = _Controller(seeded=0, detail=None)
    notifications: list[tuple[str, str]] = []
    ensured: list[int] = []

    async def _reload_selected() -> bool:
        return False

    async def _ensure_selected_detail(path_id: int) -> None:
        ensured.append(path_id)

    async def _noop_async(*_args, **_kwargs) -> None:
        return None

    def _noop() -> None:
        return None

    def _notify(message: str, kind: str) -> None:
        notifications.append((message, kind))

    ok = await run_select_path_flow(
        path_id=11,
        controller=controller,  # type: ignore[arg-type]
        state=state,
        reload_selected=_reload_selected,
        ensure_selected_detail=_ensure_selected_detail,
        reload_tracking=_noop_async,
        on_scope_selected=_noop,
        notify=_notify,
        refresh_paths_list_ui=_noop,
        open_details=_noop_async,
    )

    assert ok is True
    assert ensured == [11]
    assert ("Path selected, but selected list failed to refresh", "warning") in notifications


@pytest.mark.unit
@pytest.mark.anyio
async def test_run_unselect_path_flow_removes_detail_and_warns_when_reload_fails() -> None:
    state = PathsPageState(selected_detail_by_path_id={5: {"id": 5}})
    controller = _Controller()
    notifications: list[tuple[str, str]] = []
    refreshed: list[str] = []

    async def _reload_selected() -> bool:
        return False

    def _notify(message: str, kind: str) -> None:
        notifications.append((message, kind))

    def _refresh() -> None:
        refreshed.append("refresh")

    ok = await run_unselect_path_flow(
        path_id=5,
        controller=controller,  # type: ignore[arg-type]
        state=state,
        reload_selected=_reload_selected,
        notify=_notify,
        refresh_paths_list_ui=_refresh,
    )

    assert ok is True
    assert 5 not in state.selected_detail_by_path_id
    assert ("Path untracked, but selected list failed to refresh", "warning") in notifications
    assert refreshed == ["refresh"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_perform_create_update_delete_path_reload_page() -> None:
    controller = _Controller()
    events: list[str] = []

    async def _reload() -> None:
        events.append("reload")

    await perform_create_path(
        payload={"name": "P1", "items": [{"type": "course", "id": 1, "position": 0}]},
        controller=controller,  # type: ignore[arg-type]
        reload_page=_reload,
    )
    await perform_update_path(
        path_id=9,
        payload={"name": "P2"},
        controller=controller,  # type: ignore[arg-type]
        reload_page=_reload,
        refresh_paths_list_ui=lambda: events.append("refresh"),
    )
    await perform_delete_path(
        path_id=9,
        controller=controller,  # type: ignore[arg-type]
        reload_page=_reload,
    )

    assert events == ["reload", "reload", "refresh", "reload"]


@pytest.mark.unit
def test_refresh_paths_list_resets_visible_and_refreshes() -> None:
    ui_state = PathsPageUiState(page_size=12, visible_count=3)
    events: list[str] = []

    refresh_paths_list(
        ui_state=ui_state,
        deps=PathsListRefreshDeps(
            recompute_facet_options=lambda: events.append("facets"),
            refresh_active_filters=lambda: events.append("active"),
            refresh_paths_list_ui=lambda: events.append("list"),
        ),
    )

    assert ui_state.visible_count == 12
    assert events == ["facets", "active", "list"]


@pytest.mark.unit
def test_clear_path_filter_values_clears_controls_and_refreshes() -> None:
    search = _Control("needle")
    status = _Control("in_progress")
    sort = _Control("newest")
    scope = _Control("selected")
    calls: list[str] = []

    clear_path_filter_values(
        controls=PathsFilterControls(
            search_input=search,
            scope_filter=scope,
            status_filter=status,
            sort_filter=sort,
        ),
        deps=PathsListRefreshDeps(
            recompute_facet_options=lambda: calls.append("facets"),
            refresh_active_filters=lambda: calls.append("active"),
            refresh_paths_list_ui=lambda: calls.append("list"),
        ),
    )

    assert search.value == ""
    assert scope.value == "all"
    assert status.value == ""
    assert sort.value == ""
    assert calls == ["facets", "active", "list"]
