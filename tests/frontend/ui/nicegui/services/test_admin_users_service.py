from __future__ import annotations

import pytest

from frontend.ui.nicegui.services import admin_users_service


@pytest.mark.unit
@pytest.mark.anyio
async def test_admin_users_service_list_users_filters_non_dict_rows() -> None:
    class _Api:
        async def get(self, path: str):  # noqa: ANN001
            assert path == "/auth/users"
            return [{"username": "alice"}, "bad", {"username": "bob"}]

    out = await admin_users_service.list_users(api=_Api())  # type: ignore[arg-type]
    assert out == [{"username": "alice"}, {"username": "bob"}]


@pytest.mark.unit
@pytest.mark.anyio
async def test_admin_users_service_mutation_calls() -> None:
    calls: list[tuple[str, str, dict | None]] = []

    class _Api:
        async def post(self, path: str, payload: dict):  # noqa: ANN001
            calls.append(("POST", path, payload))
            return {}

        async def delete(self, path: str):  # noqa: ANN001
            calls.append(("DELETE", path, None))
            return {}

    api = _Api()
    await admin_users_service.create_user(api=api, username="u1", password="p1", role="user")
    await admin_users_service.reset_password(api=api, username="u1", password="p2")
    await admin_users_service.delete_user(api=api, username="u1")
    await admin_users_service.set_disabled(api=api, username="u1", disabled=True)
    assert calls == [
        ("POST", "/auth/users", {"username": "u1", "password": "p1", "role": "user"}),
        ("POST", "/auth/users/reset", {"username": "u1", "password": "p2"}),
        ("DELETE", "/auth/users/u1", None),
        ("POST", "/auth/users/disable", {"username": "u1", "disabled": True}),
    ]


@pytest.mark.unit
@pytest.mark.anyio
async def test_admin_users_service_delete_user_url_encodes_username() -> None:
    calls: list[str] = []

    class _Api:
        async def delete(self, path: str):  # noqa: ANN001
            calls.append(path)
            return {}

    await admin_users_service.delete_user(api=_Api(), username="a/b user")  # type: ignore[arg-type]
    assert calls == ["/auth/users/a%2Fb%20user"]
