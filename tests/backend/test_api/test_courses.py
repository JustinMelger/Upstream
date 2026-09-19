import pytest


pytestmark = pytest.mark.anyio


async def _login_admin(app_client):
    response = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["token"]


async def _create_user(app_client, token, username, role="user"):
    return await app_client.post(
        "/auth/users",
        json={"username": username, "password": "test-password-123", "role": role},
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
    """Any authenticated user can create courses."""
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "student1", role="user")
    user_login = await app_client.post("/auth/login", json={"username": "student1", "password": "test-password-123"})
    user_token = user_login.json()["token"]
    response = await app_client.post(
        "/courses",
        json={"title": "Intro to Python", "description": "Learn Python"},
        headers={"X-Session-Token": user_token},
    )
    assert response.status_code == 200
    assert response.json().get("title") == "Intro to Python"


@pytest.mark.integration
async def test_course_update_requires_owner_or_admin(app_client):
    """Non-admin users can only update courses they created."""
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    await _create_user(app_client, admin_token, "bob", role="user")

    alice_login = await app_client.post("/auth/login", json={"username": "alice", "password": "test-password-123"})
    bob_login = await app_client.post("/auth/login", json={"username": "bob", "password": "test-password-123"})
    alice_token = alice_login.json()["token"]
    bob_token = bob_login.json()["token"]

    created = await app_client.post(
        "/courses",
        json={"title": "Owned", "description": "Owned desc"},
        headers={"X-Session-Token": alice_token},
    )
    assert created.status_code == 200
    course_id = created.json()["id"]

    forbidden = await app_client.put(
        f"/courses/{course_id}",
        json={"title": "Hacked", "description": "Hacked desc"},
        headers={"X-Session-Token": bob_token},
    )
    assert forbidden.status_code == 403

    ok = await app_client.put(
        f"/courses/{course_id}",
        json={"title": "Updated", "description": "Updated desc"},
        headers={"X-Session-Token": alice_token},
    )
    assert ok.status_code == 200
    assert ok.json()["title"] == "Updated"


@pytest.mark.integration
async def test_get_course_not_found_returns_404(app_client):
    """Missing courses return 404."""
    token = await _login_admin(app_client)
    response = await app_client.get("/courses/999999", headers={"X-Session-Token": token})
    assert response.status_code == 404
    body = response.json()
    assert body.get("status") == "error"
    assert body.get("message") == "not_found"


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
async def test_create_course_missing_description(app_client):
    """Creating a course without a description returns 400."""
    token = await _login_admin(app_client)
    response = await app_client.post(
        "/courses",
        json={"title": "No desc", "description": ""},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 400
    body = response.json()
    assert body.get("status") == "error"
    assert body.get("message") == "missing_description"
    assert "timestamp" in body


@pytest.mark.integration
async def test_course_lifecycle(app_client):
    """Admins can create, update, fetch, and delete courses."""
    token = await _login_admin(app_client)
    create = await app_client.post(
        "/courses",
        json={
            "title": "Data Fundamentals",
            "description": "Data intro",
            "learning_outcomes": "Build and ship a basic API",
            "prerequisites": "Python basics",
            "language": "English",
            "provider": "ACME",
            "category": "Data",
            "level": "Beginner",
        },
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 200
    course = create.json()
    course_id = course["id"]

    fetch = await app_client.get(f"/courses/{course_id}", headers={"X-Session-Token": token})
    assert fetch.status_code == 200
    assert fetch.json()["title"] == "Data Fundamentals"
    assert fetch.json()["language"] == "English"
    assert "Build and ship a basic API" in fetch.json()["search_document"]

    update = await app_client.put(
        f"/courses/{course_id}",
        json={
            "title": "Data Fundamentals 2",
            "description": "Data intro updated",
            "learning_outcomes": "Design and test APIs",
            "prerequisites": "HTTP basics",
            "language": "Spanish",
        },
        headers={"X-Session-Token": token},
    )
    assert update.status_code == 200
    assert update.json()["title"] == "Data Fundamentals 2"
    assert update.json()["language"] == "Spanish"
    assert "Design and test APIs" in update.json()["search_document"]

    delete = await app_client.delete(f"/courses/{course_id}", headers={"X-Session-Token": token})
    assert delete.status_code == 200
    assert delete.json()["deleted"] is True


@pytest.mark.integration
async def test_create_course_duplicate_url_returns_409(app_client):
    """Creating a course with an existing URL returns a duplicate error."""
    token = await _login_admin(app_client)
    first = await app_client.post(
        "/courses",
        json={"title": "Course One", "description": "desc", "url": "https://example.com/course-a"},
        headers={"X-Session-Token": token},
    )
    assert first.status_code == 200

    duplicate = await app_client.post(
        "/courses",
        json={"title": "Course Two", "description": "desc", "url": " https://example.com/course-a "},
        headers={"X-Session-Token": token},
    )
    assert duplicate.status_code == 409
    body = duplicate.json()
    assert body.get("status") == "error"
    assert body.get("message") == "duplicate_url"


@pytest.mark.integration
async def test_create_course_duplicate_title_provider_returns_409(app_client):
    """Creating a course with same title/provider returns a duplicate error."""
    token = await _login_admin(app_client)
    first = await app_client.post(
        "/courses",
        json={"title": "Intro to SQL", "description": "desc", "provider": "Acme Academy"},
        headers={"X-Session-Token": token},
    )
    assert first.status_code == 200

    duplicate = await app_client.post(
        "/courses",
        json={"title": "  intro to sql  ", "description": "another", "provider": " acme academy "},
        headers={"X-Session-Token": token},
    )
    assert duplicate.status_code == 409
    body = duplicate.json()
    assert body.get("status") == "error"
    assert body.get("message") == "duplicate_title_provider"
