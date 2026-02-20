from __future__ import annotations

from frontend.ui.nicegui.pages.login.transitions import begin_login_submit, finalize_login_submit


def test_login_submit_transitions() -> None:
    start = begin_login_submit()
    assert start.loading is True
    done = finalize_login_submit()
    assert done.loading is False
