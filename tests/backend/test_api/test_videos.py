import pytest


pytestmark = pytest.mark.anyio


async def _login_admin(app_client):
    response = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["token"]


async def _create_user(app_client, token, username, role="user"):
    return await app_client.post(
        "/auth/users",
        json={"username": username, "password": "pass123", "role": role},
        headers={"X-Session-Token": token},
    )


@pytest.mark.integration
async def test_videos_requires_auth(app_client):
    response = await app_client.get("/videos")
    assert response.status_code == 401


@pytest.mark.integration
async def test_video_create_get_and_list(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    token = login.json()["token"]

    create = await app_client.post(
        "/videos",
        json={
            "title": "SQL video",
            "description": "Watch this",
            "provider": "YouTube",
            "category": "Data",
            "url": "https://www.youtube.com/watch?v=abc123",
        },
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 200
    payload = create.json()
    assert payload["title"] == "SQL video"
    assert payload["created_by"] == "alice"
    assert "preview_image_url" in payload

    detail = await app_client.get(f"/videos/{int(payload['id'])}", headers={"X-Session-Token": token})
    assert detail.status_code == 200
    assert detail.json()["provider"] == "YouTube"
    assert "preview_image_url" in detail.json()

    listing = await app_client.get("/videos", headers={"X-Session-Token": token})
    assert listing.status_code == 200
    rows = listing.json()
    assert any(int(row.get("id") or 0) == int(payload["id"]) for row in rows)
