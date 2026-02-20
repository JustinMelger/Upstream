from __future__ import annotations

import pytest

from frontend.ui.nicegui.core import errors as core_errors
from frontend.ui.nicegui.core.api_client import ApiError


class _FailingUi:
    def notify(self, *_args, **_kwargs) -> None:  # noqa: ANN002, ANN003
        raise RuntimeError("The parent element this slot belongs to has been deleted.")


@pytest.mark.unit
def test_safe_notify_ignores_missing_ui_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core_errors, "ui", _FailingUi())
    core_errors.safe_notify("hello", type="warning")


@pytest.mark.unit
def test_notify_error_uses_safe_notify_when_context_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core_errors, "ui", _FailingUi())
    core_errors.notify_error(ApiError(status_code=503, message="backend_unreachable"))
