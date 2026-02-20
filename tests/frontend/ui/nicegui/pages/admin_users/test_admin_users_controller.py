from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.admin_users.controller import AdminUsersPageController


@pytest.mark.unit
@pytest.mark.anyio
async def test_admin_users_controller_list_users_filters_non_dict_rows() -> None:
    class _Api:
        async def get(self, path: str):  # noqa: ANN001
            assert path == "/auth/users"
            return [{"username": "alice"}, "bad", {"username": "bob"}]

    c = AdminUsersPageController(api=_Api())  # type: ignore[arg-type]
    out = await c.list_users()
    assert out == [{"username": "alice"}, {"username": "bob"}]


@pytest.mark.unit
@pytest.mark.anyio
async def test_admin_users_controller_mutation_calls() -> None:
    calls: list[tuple[str, str, dict | None]] = []

    class _Api:
        async def post(self, path: str, payload: dict):  # noqa: ANN001
            calls.append(("POST", path, payload))
            return {}

        async def delete(self, path: str):  # noqa: ANN001
            calls.append(("DELETE", path, None))
            return {}

    c = AdminUsersPageController(api=_Api())  # type: ignore[arg-type]
    await c.create_user(username="u1", password="p1", role="user")
    await c.reset_password(username="u1", password="p2")
    await c.delete_user(username="u1")
    await c.set_disabled(username="u1", disabled=True)
    assert calls == [
        ("POST", "/auth/users", {"username": "u1", "password": "p1", "role": "user"}),
        ("POST", "/auth/users/reset", {"username": "u1", "password": "p2"}),
        ("DELETE", "/auth/users/u1", None),
        ("POST", "/auth/users/disable", {"username": "u1", "disabled": True}),
    ]


@pytest.mark.unit
@pytest.mark.anyio
async def test_admin_users_controller_delete_user_url_encodes_username() -> None:
    calls: list[str] = []

    class _Api:
        async def get(self, *_args, **_kwargs):  # noqa: ANN001
            return []

        async def post(self, *_args, **_kwargs):  # noqa: ANN001
            return {}

        async def delete(self, path: str):  # noqa: ANN001
            calls.append(path)
            return {}

    c = AdminUsersPageController(api=_Api())  # type: ignore[arg-type]
    await c.delete_user(username="a/b user")
    assert calls == ["/auth/users/a%2Fb%20user"]
