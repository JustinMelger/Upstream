import pytest


pytestmark = pytest.mark.anyio


async def _login_admin(app_client):
    response = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["token"]


async def _create_course(app_client, token, title):
    response = await app_client.post(
        "/courses",
        json={"title": title, "description": f"desc: {title}"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 200
    return response.json()["id"]


async def _create_user(app_client, token, username, role="user"):
    return await app_client.post(
        "/auth/users",
        json={"username": username, "password": "pass123", "role": role},
        headers={"X-Session-Token": token},
    )


@pytest.mark.integration
async def test_paths_requires_auth(app_client):
    """Path listing requires authentication."""
    response = await app_client.get("/paths")
    assert response.status_code == 401


@pytest.mark.integration
async def test_list_paths_empty(app_client):
    """Listing paths returns a list payload for authenticated users."""
    token = await _login_admin(app_client)
    response = await app_client.get("/paths", headers={"X-Session-Token": token})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.integration
async def test_create_path_missing_name(app_client):
    """Creating a path without a name returns 400."""
    token = await _login_admin(app_client)
    response = await app_client.post("/paths", json={"name": ""}, headers={"X-Session-Token": token})
    assert response.status_code == 400
    body = response.json()
    assert body.get("status") == "error"
    assert body.get("message") == "missing_name"
    assert "timestamp" in body


@pytest.mark.integration
async def test_path_lifecycle_and_selection(app_client):
    """Users can create paths, and users can select/unselect them."""
    token = await _login_admin(app_client)
    await _create_user(app_client, token, "alice", role="user")
    alice_login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    alice_token = alice_login.json()["token"]
    course_id = await _create_course(app_client, token, "Path Course 1")
    create = await app_client.post(
        "/paths",
        json={"name": "Data Path", "description": "Learn data", "course_ids": [course_id]},
        headers={"X-Session-Token": alice_token},
    )
    assert create.status_code == 200
    path_id = create.json()["id"]

    select = await app_client.post(f"/paths/{path_id}/select", headers={"X-Session-Token": token})
    assert select.status_code == 200
    assert select.json()["path_id"] == str(path_id)

    status = await app_client.post(
        f"/paths/{path_id}/status",
        json={"status": "in_progress"},
        headers={"X-Session-Token": token},
    )
    assert status.status_code == 200
    assert status.json()["updated"] == 1

    selected = await app_client.get("/paths/selected/list", headers={"X-Session-Token": token})
    assert selected.status_code == 200
    match = [item for item in selected.json() if item["id"] == path_id]
    assert match and match[0]["status"] == "in_progress"

    unselect = await app_client.post(f"/paths/{path_id}/unselect", headers={"X-Session-Token": token})
    assert unselect.status_code == 200
    assert unselect.json()["removed"] == 1

    delete = await app_client.delete(f"/paths/{path_id}", headers={"X-Session-Token": alice_token})
    assert delete.status_code == 200
    assert delete.json()["deleted"] is True


@pytest.mark.integration
async def test_path_update_requires_owner_or_admin(app_client):
    """Non-admin users can only update paths they created."""
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    await _create_user(app_client, admin_token, "bob", role="user")

    alice_login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    bob_login = await app_client.post("/auth/login", json={"username": "bob", "password": "pass123"})
    alice_token = alice_login.json()["token"]
    bob_token = bob_login.json()["token"]

    course_id = await _create_course(app_client, admin_token, "P1")
    created = await app_client.post(
        "/paths",
        json={"name": "Owned Path", "description": "", "course_ids": [course_id]},
        headers={"X-Session-Token": alice_token},
    )
    assert created.status_code == 200
    path_id = created.json()["id"]

    forbidden = await app_client.put(
        f"/paths/{path_id}",
        json={"name": "Owned Path", "description": "changed", "course_ids": [course_id]},
        headers={"X-Session-Token": bob_token},
    )
    assert forbidden.status_code == 403

    ok = await app_client.put(
        f"/paths/{path_id}",
        json={"name": "Owned Path", "description": "changed", "course_ids": [course_id]},
        headers={"X-Session-Token": alice_token},
    )
    assert ok.status_code == 200
    assert ok.json()["description"] == "changed"


@pytest.mark.integration
async def test_get_path_not_found_returns_404(app_client):
    """Missing paths return 404."""
    token = await _login_admin(app_client)
    response = await app_client.get("/paths/999999", headers={"X-Session-Token": token})
    assert response.status_code == 404
    body = response.json()
    assert body.get("status") == "error"
    assert body.get("message") == "not_found"
