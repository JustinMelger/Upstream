from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.paths import actions as paths_actions
from frontend.ui.nicegui.pages.paths.actions import build_path_card_actions, build_track_toggle, path_share_link


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
