from __future__ import annotations

from frontend.ui.nicegui.pages.admin_users.transitions import begin_admin_users_load, finalize_admin_users_load


def test_admin_users_begin_load_defaults() -> None:
    out = begin_admin_users_load()
    assert out.loading is True


def test_admin_users_finalize_load_filters_non_dict_rows() -> None:
    out = finalize_admin_users_load(rows=[{"username": "a"}, "bad", {"username": "b"}])  # type: ignore[list-item]
    assert out.loading is False
    assert out.users == [{"username": "a"}, {"username": "b"}]
