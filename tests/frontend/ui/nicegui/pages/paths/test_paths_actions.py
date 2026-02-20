from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.paths import actions as paths_actions
from frontend.ui.nicegui.pages.paths.actions import (
    build_path_card_actions,
    build_track_toggle,
    clear_path_filter_by_key,
    path_share_link,
    PathsFilterControls,
    recompute_path_status_filter,
    reset_path_filter_controls,
    resolve_paths_empty_state,
)


@pytest.mark.unit
def test_path_share_link_builds_expected_deep_link() -> None:
    assert path_share_link(path_id=42) == "/paths?path_id=42&view=full"


@pytest.mark.unit
@pytest.mark.anyio
async def test_build_track_toggle_select_branch_runs_select_and_after_hook() -> None:
    calls: list[str] = []

    async def _select(path_id: int) -> None:
        calls.append(f"select:{path_id}")
        return True

    async def _unselect(path_id: int) -> None:
        calls.append(f"unselect:{path_id}")
        return True

    def _after() -> None:
        calls.append("after")

    action, label = build_track_toggle(
        path_id=7,
        is_tracked=False,
        on_select=_select,
        on_unselect=_unselect,
        on_after_toggle=_after,
    )
    assert label == "Track"
    await action()
    assert calls == ["select:7", "after"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_build_track_toggle_unselect_branch_runs_unselect_and_after_hook() -> None:
    calls: list[str] = []

    async def _select(path_id: int) -> None:
        calls.append(f"select:{path_id}")
        return True

    async def _unselect(path_id: int) -> None:
        calls.append(f"unselect:{path_id}")
        return True

    def _after() -> None:
        calls.append("after")

    action, label = build_track_toggle(
        path_id=9,
        is_tracked=True,
        on_select=_select,
        on_unselect=_unselect,
        on_after_toggle=_after,
    )
    assert label == "Untrack"
    await action()
    assert calls == ["unselect:9", "after"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_build_track_toggle_does_not_run_after_hook_when_select_fails() -> None:
    calls: list[str] = []

    async def _select(path_id: int) -> None:
        calls.append(f"select:{path_id}")
        # Simulates a guarded callback swallowing an exception and returning None.
        return None

    async def _unselect(path_id: int) -> None:
        calls.append(f"unselect:{path_id}")
        return True

    def _after() -> None:
        calls.append("after")

    action, label = build_track_toggle(
        path_id=12,
        is_tracked=False,
        on_select=_select,
        on_unselect=_unselect,
        on_after_toggle=_after,
    )
    assert label == "Track"
    await action()
    assert calls == ["select:12"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_build_track_toggle_does_not_run_after_hook_when_unselect_returns_false() -> None:
    calls: list[str] = []

    async def _select(path_id: int) -> None:
        calls.append(f"select:{path_id}")
        return True

    async def _unselect(path_id: int) -> None:
        calls.append(f"unselect:{path_id}")
        return False

    def _after() -> None:
        calls.append("after")

    action, label = build_track_toggle(
        path_id=13,
        is_tracked=True,
        on_select=_select,
        on_unselect=_unselect,
        on_after_toggle=_after,
    )
    assert label == "Untrack"
    await action()
    assert calls == ["unselect:13"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_build_path_card_actions_wires_callbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def _fake_open_recommend_dialog(**kwargs):
        calls.append(f"recommend:{int(kwargs['path_id'])}:{kwargs['username']}")

    monkeypatch.setattr(paths_actions, "open_recommend_dialog", _fake_open_recommend_dialog)

    async def _get_user_note(path_id: int, username: str) -> str:
        return ""

    async def _save_recommendation(path_id: int, note: str):
        return {"ok": True}

    async def _on_saved() -> None:
        calls.append("saved")

    async def _get_path_detail(path_id: int) -> dict:
        calls.append(f"detail:{path_id}")
        return {"id": path_id}

    async def _on_open_edit(path_id: int, detail: dict) -> None:
        calls.append(f"edit:{path_id}:{int(detail.get('id') or 0)}")

    async def _on_delete(path_id: int) -> None:
        calls.append(f"delete:{path_id}")

    async def _on_open_details(path_id: int, mode: str) -> None:
        calls.append(f"open:{path_id}:{mode}")

    async def _on_select(path_id: int) -> None:
        calls.append(f"select:{path_id}")
        return True

    async def _on_unselect(path_id: int) -> None:
        calls.append(f"unselect:{path_id}")
        return True

    def _after() -> None:
        calls.append("after")

    cb = build_path_card_actions(
        path_id=5,
        is_tracked=False,
        username="alice",
        get_user_note=_get_user_note,
        save_recommendation=_save_recommendation,
        on_saved=_on_saved,
        get_path_detail=_get_path_detail,
        on_open_edit=_on_open_edit,
        on_delete=_on_delete,
        on_open_details=_on_open_details,
        on_select=_on_select,
        on_unselect=_on_unselect,
        on_after_toggle=_after,
    )

    assert cb.track_toggle_label == "Track"
    await cb.on_recommend()
    await cb.on_review()
    await cb.on_edit()
    await cb.on_delete()
    await cb.on_view()
    await cb.on_track_toggle()

    assert "recommend:5:alice" in calls
    assert "open:5:reviews" in calls
    assert "detail:5" in calls
    assert "edit:5:5" in calls
    assert "delete:5" in calls
    assert "open:5:full" in calls
    assert "select:5" in calls
    assert "after" in calls


class _Control:
    def __init__(self, value: str = "") -> None:
        self.value = value
        self.updated = 0

    def update(self) -> None:
        self.updated += 1


@pytest.mark.unit
def test_clear_path_filter_by_key_updates_expected_control() -> None:
    controls = PathsFilterControls(
        scope_filter=_Control("selected"),
        search_input=_Control("needle"),
        status_filter=_Control("tracked"),
        sort_filter=_Control("newest"),
    )
    assert clear_path_filter_by_key(key="search", controls=controls) is True
    assert controls.search_input.value == ""
    assert controls.search_input.updated == 1
    assert clear_path_filter_by_key(key="scope", controls=controls) is True
    assert controls.scope_filter.value == "all"
    assert controls.scope_filter.updated == 1
    assert clear_path_filter_by_key(key="status", controls=controls) is True
    assert controls.status_filter is not None and controls.status_filter.value == ""
    assert clear_path_filter_by_key(key="sort", controls=controls) is True
    assert controls.sort_filter.value == ""
    assert clear_path_filter_by_key(key="unknown", controls=controls) is False


@pytest.mark.unit
def test_reset_path_filter_controls_sets_defaults_and_updates() -> None:
    controls = PathsFilterControls(
        scope_filter=_Control("selected"),
        search_input=_Control("needle"),
        status_filter=_Control("tracked"),
        sort_filter=_Control("newest"),
    )
    reset_path_filter_controls(controls=controls)
    assert controls.scope_filter.value == "all"
    assert controls.search_input.value == ""
    assert controls.status_filter is not None and controls.status_filter.value == ""
    assert controls.sort_filter.value == ""
    assert controls.scope_filter.updated == 1
    assert controls.search_input.updated == 1
    assert controls.status_filter is not None and controls.status_filter.updated == 1
    assert controls.sort_filter.updated == 1


@pytest.mark.unit
def test_clear_path_filter_by_key_status_returns_false_when_control_missing() -> None:
    controls = PathsFilterControls(
        scope_filter=_Control("selected"),
        search_input=_Control("needle"),
        status_filter=None,
        sort_filter=_Control("newest"),
    )
    assert clear_path_filter_by_key(key="status", controls=controls) is False


@pytest.mark.unit
def test_recompute_path_status_filter_updates_and_clears_invalid_selection() -> None:
    controls = PathsFilterControls(
        scope_filter=_Control("all"),
        search_input=_Control("api"),
        status_filter=_Control("tracked"),
        sort_filter=_Control("newest"),
    )
    normalized = type("Normalized", (), dict(scope="all", search="api"))()

    def _fake_counts(**_kwargs) -> dict[str, int]:
        return {"tracked": 2, "not_tracked": 1}

    def _fake_options(*, scope_value: str, counts: dict[str, int]) -> dict[str, str]:
        return {"": "Any state", "tracked": f"Tracked ({counts.get('tracked', 0)})"}

    recompute_path_status_filter(
        controls=controls,
        paths=[],
        selected_by_id={},
        normalized_filters=normalized,
        compute_status_counts=_fake_counts,
        build_status_options=_fake_options,
    )
    assert controls.status_filter is not None
    assert controls.status_filter.value == "tracked"
    assert controls.status_filter.updated == 1

    controls.status_filter.value = "not_tracked"
    recompute_path_status_filter(
        controls=controls,
        paths=[],
        selected_by_id={},
        normalized_filters=normalized,
        compute_status_counts=_fake_counts,
        build_status_options=_fake_options,
    )
    assert controls.status_filter.value == ""


@pytest.mark.unit
def test_recompute_path_status_filter_noop_when_status_control_missing() -> None:
    controls = PathsFilterControls(
        scope_filter=_Control("all"),
        search_input=_Control("api"),
        status_filter=None,
        sort_filter=_Control(""),
    )
    normalized = type("Normalized", (), dict(scope="all", search="api"))()
    recompute_path_status_filter(
        controls=controls,
        paths=[],
        selected_by_id={},
        normalized_filters=normalized,
        compute_status_counts=lambda **_kwargs: {"tracked": 1},
        build_status_options=lambda **_kwargs: {"": "Any state", "tracked": "Tracked (1)"},
    )
    assert controls.status_filter is None


@pytest.mark.unit
def test_resolve_paths_empty_state_variants() -> None:
    assert resolve_paths_empty_state(has_rows=True, scope_value="all", has_any_filters=False, has_any_paths=True) == "has_rows"
    assert (
        resolve_paths_empty_state(has_rows=False, scope_value="selected", has_any_filters=False, has_any_paths=True)
        == "selected_empty"
    )
    assert (
        resolve_paths_empty_state(has_rows=False, scope_value="all", has_any_filters=False, has_any_paths=False)
        == "catalog_empty"
    )
    assert (
        resolve_paths_empty_state(has_rows=False, scope_value="all", has_any_filters=True, has_any_paths=True)
        == "filters_empty"
    )
