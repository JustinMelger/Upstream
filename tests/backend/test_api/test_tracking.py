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
    """Personal learning reads require authentication."""
    response = await app_client.get("/learning/items?view=tracked")
    assert response.status_code == 401


@pytest.mark.integration
async def test_tracking_lifecycle(app_client):
    """Users can set, read, and delete tracking entries."""
    token = await _login_admin(app_client)
    course_id = await _create_course(app_client, token, "Tracking Course 1")
    create = await app_client.post(
        "/tracking",
        json={"course_id": course_id, "status": "interested"},
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 200
    assert create.json()["status"] == "interested"

    listing = await app_client.get("/learning/items?view=tracked", headers={"X-Session-Token": token})
    assert listing.status_code == 200
    assert any(item["id"] == course_id for item in listing.json()["items"])

    delete = await app_client.post(
        "/tracking/delete",
        json={"course_id": course_id},
        headers={"X-Session-Token": token},
    )
    assert delete.status_code == 200
    assert delete.json()["removed"] == 1

    after_delete = await app_client.get("/learning/items?view=tracked", headers={"X-Session-Token": token})
    assert all(item["id"] != course_id for item in after_delete.json()["items"])
