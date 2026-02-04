
import pytest

from backend.database.db import get_conn


def _login_admin(app_client):
    response = app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["token"]


@pytest.mark.integration
def test_bootstrap_login(app_client):
    """Bootstrap admin login succeeds when no users exist."""
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions")
        conn.execute("DELETE FROM users")
        conn.commit()

    response = app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("token")
    assert data.get("role") == "admin"


@pytest.mark.integration
def test_create_user(app_client):
    """Admin can create a new user or get a conflict if it exists."""
    login = app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = login.json()["token"]
    response = app_client.post(
        "/auth/users",
        json={"username": "user1", "password": "pass123", "role": "user"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code in (200, 409)


@pytest.mark.integration
def test_login_missing_fields(app_client):
    """Login requires username and password."""
    response = app_client.post("/auth/login", json={"username": "", "password": ""})
    assert response.status_code == 400
    assert response.json().get("detail") == "missing_fields"


@pytest.mark.integration
def test_me_requires_auth(app_client):
    """The /auth/me endpoint rejects missing sessions."""
    response = app_client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.integration
def test_me_returns_user(app_client):
    """The /auth/me endpoint returns current user metadata."""
    token = _login_admin(app_client)
    response = app_client.get("/auth/me", headers={"X-Session-Token": token})
    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "admin"
    assert payload["role"] == "admin"
    assert payload["expires_at"]


@pytest.mark.integration
def test_logout_revokes_sessions(app_client):
    """Logout revokes the user's sessions."""
    token = _login_admin(app_client)
    response = app_client.post("/auth/logout", headers={"X-Session-Token": token})
    assert response.status_code == 200
    assert response.json().get("revoked") >= 1


@pytest.mark.integration
def test_create_user_invalid_role(app_client):
    """Creating a user with an invalid role returns 400."""
    token = _login_admin(app_client)
    response = app_client.post(
        "/auth/users",
        json={"username": "role_user", "password": "pass123", "role": "manager"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 400
    assert response.json().get("detail") == "invalid_role"


@pytest.mark.integration
def test_delete_user_cannot_delete_self(app_client):
    """Admins cannot delete themselves."""
    token = _login_admin(app_client)
    response = app_client.delete("/auth/users/admin", headers={"X-Session-Token": token})
    assert response.status_code == 400
    assert response.json().get("detail") == "cannot_delete_self"


@pytest.mark.integration
def test_disable_user_cannot_disable_self(app_client):
    """Admins cannot disable their own account."""
    token = _login_admin(app_client)
    response = app_client.post(
        "/auth/users/disable",
        json={"username": "admin", "disabled": True},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 400
    assert response.json().get("detail") == "cannot_disable_self"


@pytest.mark.integration
def test_reset_password_not_found(app_client):
    """Resetting a missing user returns a 404."""
    token = _login_admin(app_client)
    response = app_client.post(
        "/auth/users/reset",
        json={"username": "missing-user", "password": "newpass"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 404
    assert response.json().get("detail") == "user_not_found"
