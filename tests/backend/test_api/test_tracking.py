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


@pytest.mark.integration
async def test_tracking_requires_auth(app_client):
    """Tracking listing requires authentication."""
    response = await app_client.get("/tracking")
    assert response.status_code == 401


@pytest.mark.integration
async def test_tracking_lifecycle(app_client):
    """Users can set, list, and delete tracking entries."""
    token = await _login_admin(app_client)
    course_id = await _create_course(app_client, token, "Tracking Course 1")
    create = await app_client.post(
        "/tracking",
        json={"course_id": course_id, "status": "interested"},
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 200
    assert create.json()["status"] == "interested"

    listing = await app_client.get("/tracking", headers={"X-Session-Token": token})
    assert listing.status_code == 200
    assert len(listing.json()) >= 1

    delete = await app_client.post(
        "/tracking/delete",
        json={"course_id": course_id},
        headers={"X-Session-Token": token},
    )
    assert delete.status_code == 200
    assert delete.json()["removed"] == 1


@pytest.mark.integration
async def test_tracking_stats_permissions(app_client):
    """Tracking stats are restricted to admins for team views."""
    admin_token = await _login_admin(app_client)
    create_user = await app_client.post(
        "/auth/users",
        json={"username": "viewer1", "password": "pass123", "role": "user"},
        headers={"X-Session-Token": admin_token},
    )
    assert create_user.status_code in (200, 409)
    user_login = await app_client.post("/auth/login", json={"username": "viewer1", "password": "pass123"})
    user_token = user_login.json()["token"]

    response = await app_client.get("/tracking/stats", headers={"X-Session-Token": user_token})
    assert response.status_code == 403
    assert response.json().get("message") == "admin_required"

    admin_stats = await app_client.get("/tracking/stats", headers={"X-Session-Token": admin_token})
    assert admin_stats.status_code == 200
