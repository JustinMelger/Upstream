from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.admin_users.controller import AdminUsersPageController


@pytest.mark.unit
@pytest.mark.anyio
async def test_admin_users_controller_list_users_filters_non_dict_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    from frontend.ui.nicegui.pages.admin_users import controller as admin_users_controller

    calls: list[object] = []

    async def _list_users(*, api):  # noqa: ANN001
        calls.append(api)
        return [{"username": "alice"}, {"username": "bob"}]

    monkeypatch.setattr(admin_users_controller, "list_users", _list_users)

    marker_api = object()
    c = AdminUsersPageController(api=marker_api)  # type: ignore[arg-type]
    out = await c.list_users()

    assert out == [{"username": "alice"}, {"username": "bob"}]
    assert calls == [marker_api]


@pytest.mark.unit
@pytest.mark.anyio
async def test_admin_users_controller_mutation_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    from frontend.ui.nicegui.pages.admin_users import controller as admin_users_controller

    calls: list[tuple[str, str, object]] = []

    async def _create_user(*, api, username: str, password: str, role: str):  # noqa: ANN001
        calls.append(("create", username, api))

    async def _reset_password(*, api, username: str, password: str):  # noqa: ANN001
        calls.append(("reset", username, api))

    async def _delete_user(*, api, username: str):  # noqa: ANN001
        calls.append(("delete", username, api))

    async def _set_disabled(*, api, username: str, disabled: bool):  # noqa: ANN001
        calls.append(("disabled", f"{username}:{disabled}", api))

    monkeypatch.setattr(admin_users_controller, "create_user", _create_user)
    monkeypatch.setattr(admin_users_controller, "reset_password", _reset_password)
    monkeypatch.setattr(admin_users_controller, "delete_user", _delete_user)
    monkeypatch.setattr(admin_users_controller, "set_disabled", _set_disabled)

    marker_api = object()
    c = AdminUsersPageController(api=marker_api)  # type: ignore[arg-type]
    await c.create_user(username="u1", password="p1", role="user")
    await c.reset_password(username="u1", password="p2")
    await c.delete_user(username="u1")
    await c.set_disabled(username="u1", disabled=True)
    assert calls == [
        ("create", "u1", marker_api),
        ("reset", "u1", marker_api),
        ("delete", "u1", marker_api),
        ("disabled", "u1:True", marker_api),
    ]


@pytest.mark.unit
@pytest.mark.anyio
async def test_admin_users_controller_delete_user_url_encodes_username(monkeypatch: pytest.MonkeyPatch) -> None:
    from frontend.ui.nicegui.pages.admin_users import controller as admin_users_controller

    calls: list[str] = []

    async def _delete_user(*, api, username: str):  # noqa: ANN001
        calls.append(str(username))

    monkeypatch.setattr(admin_users_controller, "delete_user", _delete_user)
    c = AdminUsersPageController(api=object())  # type: ignore[arg-type]
    await c.delete_user(username="a/b user")

    assert calls == ["a/b user"]
