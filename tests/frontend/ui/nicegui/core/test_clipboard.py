from __future__ import annotations

import pytest

from frontend.ui.nicegui.core import clipboard


@pytest.mark.unit
def test_copy_text_to_clipboard_runs_js_and_notifies(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, str] = {}

    def _fake_run_javascript(script: str) -> None:
        calls["script"] = script

    def _fake_notify(message: str, *, type: str) -> None:  # noqa: A002
        calls["message"] = message
        calls["type"] = type

    monkeypatch.setattr(clipboard.ui, "run_javascript", _fake_run_javascript)
    monkeypatch.setattr(clipboard, "safe_notify", _fake_notify)

    clipboard.copy_text_to_clipboard(text="https://example.com")

    assert "navigator.clipboard.writeText(" in calls["script"]
    assert calls["message"] == "Link copied"
    assert calls["type"] == "positive"
