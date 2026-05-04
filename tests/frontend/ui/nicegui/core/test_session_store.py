from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.core.session_store import SessionStore


@pytest.mark.unit
@pytest.mark.anyio
async def test_session_store_login_clears_stale_state_and_skips_old_token_header(monkeypatch: pytest.MonkeyPatch) -> None:
    storage: dict[str, object] = {
        "session_token": "old-token",
        "current_user": {"username": "alice", "role": "user"},
    }
    monkeypatch.setattr(
        "frontend.ui.nicegui.core.session_store.app",
        SimpleNamespace(storage=SimpleNamespace(user=storage)),
    )

    calls: list[tuple[str, dict[str, Any], str | None]] = []

    class _Api:
        async def post(self, path: str, payload: dict[str, Any], *, token_override: str | None = None) -> Any:
            calls.append((path, payload, token_override))
            assert "current_user" not in storage
            assert "session_token" not in storage
            return {"token": "new-token"}

        async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:  # noqa: ARG002
            assert path == "/auth/me"
            return {"username": "bob", "role": "user"}

    store = SessionStore()
    me = await store.login(_Api(), username="bob", password="secret")  # type: ignore[arg-type]

    assert calls == [("/auth/login", {"username": "bob", "password": "secret"}, "")]
    assert me == {"username": "bob", "role": "user"}
    assert storage["session_token"] == "new-token"
    assert storage["current_user"] == {"username": "bob", "role": "user"}


@pytest.mark.unit
@pytest.mark.anyio
async def test_session_store_login_restores_previous_session_when_login_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    storage: dict[str, object] = {
        "session_token": "old-token",
        "current_user": {"username": "alice", "role": "user"},
    }
    monkeypatch.setattr(
        "frontend.ui.nicegui.core.session_store.app",
        SimpleNamespace(storage=SimpleNamespace(user=storage)),
    )

    class _Api:
        async def post(self, path: str, payload: dict[str, Any], *, token_override: str | None = None) -> Any:  # noqa: ARG002
            assert path == "/auth/login"
            assert token_override == ""
            assert "current_user" not in storage
            assert "session_token" not in storage
            raise ApiError(status_code=401, message="bad_credentials")

    store = SessionStore()
    with pytest.raises(ApiError, match="bad_credentials"):
        await store.login(_Api(), username="bob", password="wrong")  # type: ignore[arg-type]

    assert storage["session_token"] == "old-token"
    assert storage["current_user"] == {"username": "alice", "role": "user"}


@pytest.mark.unit
def test_session_store_set_token_clears_cached_user_when_token_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    storage: dict[str, object] = {
        "session_token": "old-token",
        "current_user": {"username": "alice", "role": "user"},
    }
    monkeypatch.setattr(
        "frontend.ui.nicegui.core.session_store.app",
        SimpleNamespace(storage=SimpleNamespace(user=storage)),
    )

    store = SessionStore()
    store.set_token("new-token")

    assert storage["session_token"] == "new-token"
    assert "current_user" not in storage
