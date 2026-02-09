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
async def test_courses_requires_auth(app_client):
    """Course listing requires authentication."""
    response = await app_client.get("/courses")
    assert response.status_code == 401


@pytest.mark.integration
async def test_list_courses_empty(app_client):
    """Listing courses returns a list payload for authenticated users."""
    token = await _login_admin(app_client)
    response = await app_client.get("/courses", headers={"X-Session-Token": token})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.integration
async def test_create_course_admin_only(app_client):
    """Non-admin users cannot create courses."""
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "student1", role="user")
    user_login = await app_client.post("/auth/login", json={"username": "student1", "password": "pass123"})
    user_token = user_login.json()["token"]
    response = await app_client.post(
        "/courses",
        json={"title": "Intro to Python"},
        headers={"X-Session-Token": user_token},
    )
    assert response.status_code == 403
    assert response.json().get("detail") == "admin_required"


@pytest.mark.integration
async def test_create_course_missing_title(app_client):
    """Creating a course without a title returns 400."""
    token = await _login_admin(app_client)
    response = await app_client.post("/courses", json={"title": ""}, headers={"X-Session-Token": token})
    assert response.status_code == 400
    body = response.json()
    assert body.get("status") == "error"
    assert body.get("message") == "missing_title"
    assert "timestamp" in body


@pytest.mark.integration
async def test_course_lifecycle(app_client):
    """Admins can create, update, fetch, and delete courses."""
    token = await _login_admin(app_client)
    create = await app_client.post(
        "/courses",
        json={"title": "Data Fundamentals", "provider": "ACME", "category": "Data", "level": "Beginner"},
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 200
    course = create.json()
    course_id = course["id"]

    fetch = await app_client.get(f"/courses/{course_id}", headers={"X-Session-Token": token})
    assert fetch.status_code == 200
    assert fetch.json()["title"] == "Data Fundamentals"

    update = await app_client.put(
        f"/courses/{course_id}",
        json={"title": "Data Fundamentals 2"},
        headers={"X-Session-Token": token},
    )
    assert update.status_code == 200
    assert update.json()["title"] == "Data Fundamentals 2"

    delete = await app_client.delete(f"/courses/{course_id}", headers={"X-Session-Token": token})
    assert delete.status_code == 200
    assert delete.json()["deleted"] is True
