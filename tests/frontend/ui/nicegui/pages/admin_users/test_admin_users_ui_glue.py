from __future__ import annotations

from frontend.ui.nicegui.pages.admin_users.ui_glue import _filter_users, _user_row


def test_admin_users_filter_users_by_username_or_role() -> None:
    users = [
        {"username": "alice", "role": "admin"},
        {"username": "bob", "role": "user"},
    ]
    assert [u["username"] for u in _filter_users(users, "ali")] == ["alice"]
    assert [u["username"] for u in _filter_users(users, "USER")] == ["bob"]
    assert _filter_users(users, "") == users


def test_admin_users_user_row_maps_disabled_and_time_fields() -> None:
    row = _user_row(
        {
            "username": "alice",
            "role": "admin",
            "created_at": "",
            "updated_at": "",
            "last_login_at": "",
            "disabled": True,
        }
    )
    assert row["username"] == "alice"
    assert row["role"] == "admin"
    assert row["disabled"] == "Yes"
