"""Account permissions and serialized access changes on disposable PostgreSQL."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from backend.database.async_repositories.auth import AuthRepository


pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def login(client, username="admin", password="admin"):
    """Authenticate and retain a header session for subsequent assertions."""
    response = await client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"X-Session-Token": response.json()["token"]}


async def accounts(client, role="user"):
    """Create a second account with a live session."""
    admin = await login(client)
    response = await client.post(
        "/auth/users",
        headers=admin,
        json={"username": "Alice", "password": "test-password-123", "role": role},
    )
    assert response.status_code == 200
    return admin, await login(client, "Alice", "test-password-123")


async def test_role_change_preserves_sessions_and_immediately_changes_permissions(app_client):
    """The same session gains and loses authority without reauthentication."""
    admin, member = await accounts(app_client)
    assert (await app_client.get("/auth/users", headers=member)).status_code == 403
    for role in ("admin", "admin", "user"):
        response = await app_client.patch("/auth/users/aLiCe/role", headers=admin, json={"role": role})
        assert response.status_code == 200, response.text
        assert response.json() == {"username": "Alice", "role": role}
        assert (await app_client.get("/auth/me", headers=member)).json()["role"] == role
        assert (await app_client.get("/auth/users", headers=member)).status_code == (200 if role == "admin" else 403)


async def test_role_validation_and_authorization(app_client):
    """Reject unauthorized, invalid, missing and self-targeted role changes."""
    admin, member = await accounts(app_client)
    assert (await app_client.patch("/auth/users/Alice/role", json={"role": "admin"})).status_code == 401
    assert (await app_client.patch("/auth/users/admin/role", headers=member, json={"role": "user"})).status_code == 403
    for payload in ({}, {"role": "owner"}, {"role": None}, {"role": 1}):
        assert (await app_client.patch("/auth/users/Alice/role", headers=admin, json=payload)).status_code == 422
    assert (await app_client.patch("/auth/users/missing/role", headers=admin, json={"role": "admin"})).status_code == 404
    for role in ("admin", "user"):
        response = await app_client.patch("/auth/users/ADMIN/role", headers=admin, json={"role": role})
        assert response.status_code == 400
        assert "cannot_change_own_role" in response.text


async def test_browser_role_change_requires_csrf(app_client):
    """Browser role mutations retain same-origin and CSRF enforcement."""
    await accounts(app_client)
    response = await app_client.post(
        "/auth/browser/login",
        headers={"Origin": "http://localhost:8080"},
        json={"username": "admin", "password": "admin"},
    )
    assert response.status_code == 200
    headers = {"Origin": "http://localhost:8080", "X-CSRF-Token": response.json()["csrf_token"]}
    assert (await app_client.patch("/auth/users/Alice/role", json={"role": "admin"})).status_code == 403
    assert (
        await app_client.patch(
            "/auth/users/Alice/role", headers=headers | {"Origin": "https://evil.example"}, json={"role": "admin"}
        )
    ).status_code == 403
    assert (await app_client.patch("/auth/users/Alice/role", headers=headers, json={"role": "admin"})).status_code == 200


async def test_disabled_admin_does_not_count_or_become_enabled_by_promotion(app_client):
    """Role edits never enable disabled accounts or allow them to administer."""
    admin, member = await accounts(app_client)
    assert (
        await app_client.post("/auth/users/disable", headers=admin, json={"username": "Alice", "disabled": True})
    ).status_code == 200
    assert (await app_client.patch("/auth/users/Alice/role", headers=admin, json={"role": "admin"})).status_code == 200
    rows = (await app_client.get("/auth/users", headers=admin)).json()
    assert next(row for row in rows if row["username"] == "Alice")["disabled"] is True
    assert (await app_client.get("/auth/users", headers=member)).status_code == 401
    for action in ("demote", "disable", "delete"):
        assert (await change(app_client, admin, "admin", action)).status_code == 400


@pytest.mark.parametrize("action", ["demote", "disable", "delete"])
async def test_last_admin_guard_rejects_mutation(app_client, monkeypatch, action):
    """Exercise the defensive count guard independently of self-protection."""
    admin, _ = await accounts(app_client, role="admin")
    monkeypatch.setattr(AuthRepository, "enabled_admin_count", AsyncMock(return_value=1))
    response = await change(app_client, admin, "Alice", action)
    assert response.status_code == 409
    assert "last_admin_required" in response.text
    rows = (await app_client.get("/auth/users", headers=admin)).json()
    alice = next(row for row in rows if row["username"] == "Alice")
    assert alice["role"] == "admin" and not alice["disabled"]


async def test_admin_count_excludes_disabled_accounts(app_client, sessionmaker):
    """Only enabled administrators contribute to the retained-access count."""
    admin, _ = await accounts(app_client, role="admin")
    await change(app_client, admin, "Alice", "disable")
    async with sessionmaker() as session:
        assert await AuthRepository(session).enabled_admin_count() == 1


async def change(client, headers, target, action):
    """Exercise one account mutation using a previously issued session."""
    if action == "demote":
        return await client.patch(f"/auth/users/{target}/role", headers=headers, json={"role": "user"})
    if action == "disable":
        return await client.post("/auth/users/disable", headers=headers, json={"username": target, "disabled": True})
    return await client.delete(f"/auth/users/{target}", headers=headers)


@pytest.mark.parametrize("actions", [("demote", "demote"), ("demote", "disable"), ("disable", "delete"), ("delete", "demote")])
async def test_concurrent_account_changes_keep_an_enabled_admin(app_client, actions):
    """Competing administrators cannot remove each other's access together."""
    admin, alice = await accounts(app_client, role="admin")
    responses = await asyncio.wait_for(
        asyncio.gather(
            change(app_client, admin, "Alice", actions[0]),
            change(app_client, alice, "admin", actions[1]),
        ),
        timeout=10,
    )
    assert sum(response.status_code == 200 for response in responses) == 1
    assert all(response.status_code in (200, 401, 403, 409) for response in responses)
    survivor = admin if responses[0].status_code == 200 else alice
    rows = (await app_client.get("/auth/users", headers=survivor)).json()
    assert sum(row["role"] == "admin" and not row["disabled"] for row in rows) == 1
