import pytest


pytestmark = pytest.mark.anyio


async def _login_admin(app_client):
    response = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["token"]


@pytest.mark.integration
async def test_bootstrap_login(app_client):
    """Bootstrap admin login succeeds when no users exist."""
    response = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("token")
    assert data.get("role") == "admin"


@pytest.mark.integration
async def test_create_user(app_client):
    """Admin can create a new user or get a conflict if it exists."""
    login = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = login.json()["token"]
    response = await app_client.post(
        "/auth/users",
        json={"username": "user1", "password": "pass123", "role": "user"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code in (200, 409)


@pytest.mark.integration
async def test_login_missing_fields(app_client):
    """Login rejects blank credentials during request validation."""
    response = await app_client.post("/auth/login", json={"username": "", "password": ""})
    assert response.status_code == 422


@pytest.mark.integration
async def test_me_requires_auth(app_client):
    """The /auth/me endpoint rejects missing sessions."""
    response = await app_client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.integration
async def test_me_returns_user(app_client):
    """The /auth/me endpoint returns current user metadata."""
    token = await _login_admin(app_client)
    response = await app_client.get("/auth/me", headers={"X-Session-Token": token})
    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "admin"
    assert payload["role"] == "admin"
    assert payload["expires_at"]


@pytest.mark.integration
async def test_logout_revokes_sessions(app_client):
    """Logout revokes the user's sessions."""
    token = await _login_admin(app_client)
    response = await app_client.post("/auth/logout", headers={"X-Session-Token": token})
    assert response.status_code == 200
    assert response.json().get("revoked") >= 1


@pytest.mark.integration
async def test_change_password_rejects_incorrect_current_password(app_client):
    """An incorrect current password cannot change the account password."""
    token = await _login_admin(app_client)
    response = await app_client.post(
        "/auth/password/change",
        json={"current_password": "incorrect", "new_password": "newpass123"},
        headers={"X-Session-Token": token},
    )

    assert response.status_code == 401
    assert response.json().get("message") == "invalid_credentials"
    assert (await app_client.get("/auth/me", headers={"X-Session-Token": token})).status_code == 200
    assert (await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})).status_code == 200
    assert (await app_client.post("/auth/login", json={"username": "admin", "password": "newpass123"})).status_code == 401


@pytest.mark.integration
async def test_create_user_invalid_role(app_client):
    """Creating a user with an invalid role fails request validation."""
    token = await _login_admin(app_client)
    response = await app_client.post(
        "/auth/users",
        json={"username": "role_user", "password": "pass123", "role": "manager"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 422


@pytest.mark.integration
async def test_delete_user_cannot_delete_self(app_client):
    """Admins cannot delete themselves."""
    token = await _login_admin(app_client)
    response = await app_client.delete("/auth/users/admin", headers={"X-Session-Token": token})
    assert response.status_code == 400
    assert response.json().get("message") == "cannot_delete_self"


@pytest.mark.integration
async def test_disable_user_cannot_disable_self(app_client):
    """Admins cannot disable their own account."""
    token = await _login_admin(app_client)
    response = await app_client.post(
        "/auth/users/disable",
        json={"username": "admin", "disabled": True},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 400
    assert response.json().get("message") == "cannot_disable_self"


@pytest.mark.integration
async def test_reset_password_not_found(app_client):
    """Resetting a missing user returns a 404."""
    token = await _login_admin(app_client)
    response = await app_client.post(
        "/auth/users/reset",
        json={"username": "missing-user", "password": "newpass"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 404
    assert response.json().get("message") == "user_not_found"


@pytest.mark.integration
async def test_login_with_different_username_casing_uses_canonical_user_identity(app_client):
    """Case-insensitive login should still create a canonical session identity."""
    admin_token = await _login_admin(app_client)
    created = await app_client.post(
        "/auth/users",
        json={"username": "Alice", "password": "pass123", "role": "user"},
        headers={"X-Session-Token": admin_token},
    )
    assert created.status_code == 200

    login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    assert login.status_code == 200
    payload = login.json()
    assert payload["username"] == "Alice"

    token = payload["token"]
    me = await app_client.get("/auth/me", headers={"X-Session-Token": token})
    assert me.status_code == 200
    assert me.json()["username"] == "Alice"

    logout = await app_client.post("/auth/logout", headers={"X-Session-Token": token})
    assert logout.status_code == 200
    assert logout.json()["revoked"] >= 1
