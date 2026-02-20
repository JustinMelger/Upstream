from __future__ import annotations

import pytest

from frontend.ui.nicegui.core import errors as core_errors
from frontend.ui.nicegui.pages.learning import sections as learning_sections
from frontend.ui.nicegui.pages.learning.ui_glue import resolve_tracking_status_value


class _FakeSelect:
    def __init__(self, value: str):
        self.value = value
        self.handlers: dict[str, object] = {}
        self.enabled = True
        self.updated = 0

    def props(self, _value: str):
        return self

    def tooltip(self, _value: str):
        return self

    def on(self, event: str, cb):
        self.handlers[event] = cb
        return self

    def disable(self) -> None:
        self.enabled = False

    def enable(self) -> None:
        self.enabled = True

    def update(self) -> None:
        self.updated += 1


class _FakeUi:
    def __init__(self, select: _FakeSelect):
        self._select = select
        self.notifications: list[str] = []

    def select(self, **_kwargs):
        return self._select

    def notify(self, msg: str, **_kwargs) -> None:
        self.notifications.append(msg)


@pytest.mark.unit
@pytest.mark.anyio
async def test_render_tracking_status_select_rolls_back_on_set_error(monkeypatch: pytest.MonkeyPatch) -> None:
    select = _FakeSelect(value="interested")
    fake_ui = _FakeUi(select=select)
    monkeypatch.setattr(learning_sections, "ui", fake_ui)
    monkeypatch.setattr(core_errors, "ui", fake_ui)

    async def _set_status(_cid: int, _value: str) -> None:
        raise RuntimeError("boom")

    async def _clear_status(_cid: int) -> None:
        return None

    learning_sections.render_tracking_status_select(
        course_id=7,
        current_status="interested",
        options_map={"": "Not tracked", "interested": "Interested", "completed": "Completed"},
        resolve_status_value=resolve_tracking_status_value,
        on_set_status=_set_status,
        on_clear_status=_clear_status,
    )
    handler = select.handlers["update:model-value"]

    with pytest.raises(RuntimeError):
        await handler("completed")

    assert select.value == "interested"
    assert select.enabled is True
    assert select.updated >= 2


@pytest.mark.unit
@pytest.mark.anyio
async def test_render_tracking_status_select_rejects_invalid_and_restores_previous(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    select = _FakeSelect(value="in_progress")
    fake_ui = _FakeUi(select=select)
    monkeypatch.setattr(learning_sections, "ui", fake_ui)
    monkeypatch.setattr(core_errors, "ui", fake_ui)

    async def _set_status(_cid: int, _value: str) -> None:
        raise AssertionError("should not be called")

    async def _clear_status(_cid: int) -> None:
        raise AssertionError("should not be called")

    learning_sections.render_tracking_status_select(
        course_id=8,
        current_status="in_progress",
        options_map={"": "Not tracked", "in_progress": "In progress"},
        resolve_status_value=resolve_tracking_status_value,
        on_set_status=_set_status,
        on_clear_status=_clear_status,
    )
    handler = select.handlers["update:model-value"]
    await handler("not_a_valid_status")

    assert select.value == "in_progress"
    assert any("Invalid status" in msg for msg in fake_ui.notifications)
