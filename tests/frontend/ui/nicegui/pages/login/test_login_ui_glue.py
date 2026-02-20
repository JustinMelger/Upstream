from __future__ import annotations

from frontend.ui.nicegui.pages.login.ui_glue import credentials_valid, normalize_credentials


def test_login_normalize_credentials() -> None:
    u, p = normalize_credentials(username=" alice ", password="  secret")
    assert u == "alice"
    assert p == "  secret"


def test_login_credentials_valid() -> None:
    assert credentials_valid(username="alice", password="x") is True
    assert credentials_valid(username="", password="x") is False
    assert credentials_valid(username="alice", password="") is False
