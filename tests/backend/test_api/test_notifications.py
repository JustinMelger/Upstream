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
async def test_notifications_requires_auth(app_client):
    response = await app_client.get("/notifications/activity")
    assert response.status_code == 401


@pytest.mark.integration
async def test_notifications_activity_includes_course_shares(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    await _create_user(app_client, admin_token, "bob", role="user")

    alice_login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    bob_login = await app_client.post("/auth/login", json={"username": "bob", "password": "pass123"})
    alice_token = alice_login.json()["token"]
    bob_token = bob_login.json()["token"]

    create_course = await app_client.post(
        "/courses",
        json={"title": "Activity Course", "description": "desc", "url": "https://example.com/activity"},
        headers={"X-Session-Token": alice_token},
    )
    assert create_course.status_code == 200
    course_id = int(create_course.json()["id"])

    alice_feed = await app_client.get("/notifications/activity", headers={"X-Session-Token": alice_token})
    assert alice_feed.status_code == 200
    alice_rows = list(alice_feed.json() or [])
    assert alice_rows == []

    bob_feed = await app_client.get("/notifications/activity", headers={"X-Session-Token": bob_token})
    assert bob_feed.status_code == 200
    bob_rows = list(bob_feed.json() or [])
    assert bob_rows == []

    bob_team_feed = await app_client.get(
        "/notifications/activity",
        params={"scope": "team"},
        headers={"X-Session-Token": bob_token},
    )
    assert bob_team_feed.status_code == 200
    bob_team_rows = list(bob_team_feed.json() or [])
    assert bob_team_rows
    bob_team_types = {str(r.get("event_type") or "") for r in bob_team_rows}
    assert "course_shared" in bob_team_types


@pytest.mark.integration
async def test_notifications_activity_includes_video_shares(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    await _create_user(app_client, admin_token, "bob", role="user")

    alice_login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    bob_login = await app_client.post("/auth/login", json={"username": "bob", "password": "pass123"})
    alice_token = alice_login.json()["token"]
    bob_token = bob_login.json()["token"]

    create_video = await app_client.post(
        "/videos",
        json={
            "title": "Shared video",
            "description": "desc",
            "provider": "YouTube",
            "category": "Programming",
            "url": "https://www.youtube.com/watch?v=shared123",
        },
        headers={"X-Session-Token": alice_token},
    )
    assert create_video.status_code == 200

    bob_team_feed = await app_client.get(
        "/notifications/activity",
        params={"scope": "team"},
        headers={"X-Session-Token": bob_token},
    )
    assert bob_team_feed.status_code == 200
    bob_team_rows = list(bob_team_feed.json() or [])
    assert bob_team_rows
    bob_team_types = {str(r.get("event_type") or "") for r in bob_team_rows}
    assert "video_shared" in bob_team_types


@pytest.mark.integration
async def test_notifications_activity_includes_course_path_and_article_ratings(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    await _create_user(app_client, admin_token, "bob", role="user")

    alice_login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    bob_login = await app_client.post("/auth/login", json={"username": "bob", "password": "pass123"})
    alice_token = alice_login.json()["token"]
    bob_token = bob_login.json()["token"]

    create_course = await app_client.post(
        "/courses",
        json={"title": "Rated Course", "description": "desc", "url": "https://example.com/rated-course"},
        headers={"X-Session-Token": alice_token},
    )
    assert create_course.status_code == 200
    course_id = int(create_course.json()["id"])

    create_path = await app_client.post(
        "/paths",
        json={"name": "Rated Path", "description": "desc", "items": [{"type": "course", "id": course_id, "position": 0}]},
        headers={"X-Session-Token": alice_token},
    )
    assert create_path.status_code == 200
    path_id = int(create_path.json()["id"])

    create_article = await app_client.post(
        "/articles",
        json={"title": "Rated Article", "url": "https://example.com/article", "tags": "test"},
        headers={"X-Session-Token": alice_token},
    )
    assert create_article.status_code == 200
    article_id = int(create_article.json()["id"])

    course_review = await app_client.post(
        f"/courses/{course_id}/reviews",
        json={"rating": 5, "text": "Excellent"},
        headers={"X-Session-Token": bob_token},
    )
    assert course_review.status_code == 200

    path_review = await app_client.post(
        f"/paths/{path_id}/reviews",
        json={"rating": 4, "text": "Solid"},
        headers={"X-Session-Token": bob_token},
    )
    assert path_review.status_code == 200

    article_review = await app_client.post(
        f"/articles/{article_id}/reviews",
        json={"rating": 5, "text": "Helpful"},
        headers={"X-Session-Token": bob_token},
    )
    assert article_review.status_code == 200

    alice_feed = await app_client.get("/notifications/activity", headers={"X-Session-Token": alice_token})
    assert alice_feed.status_code == 200
    alice_rows = list(alice_feed.json() or [])
    assert alice_rows
    alice_types = {str(r.get("event_type") or "") for r in alice_rows}
    assert "your_course_rated" in alice_types
    assert "your_path_rated" in alice_types
    assert "your_article_rated" in alice_types


@pytest.mark.integration
async def test_notifications_activity_includes_video_ratings(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    await _create_user(app_client, admin_token, "bob", role="user")

    alice_login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    bob_login = await app_client.post("/auth/login", json={"username": "bob", "password": "pass123"})
    alice_token = alice_login.json()["token"]
    bob_token = bob_login.json()["token"]

    create_video = await app_client.post(
        "/videos",
        json={
            "title": "Rated Video",
            "description": "desc",
            "provider": "YouTube",
            "category": "Programming",
            "url": "https://www.youtube.com/watch?v=rated-video",
        },
        headers={"X-Session-Token": alice_token},
    )
    assert create_video.status_code == 200
    video_id = int(create_video.json()["id"])

    video_review = await app_client.post(
        f"/videos/{video_id}/reviews",
        json={"rating": 5, "text": "Helpful"},
        headers={"X-Session-Token": bob_token},
    )
    assert video_review.status_code == 200

    alice_feed = await app_client.get("/notifications/activity", headers={"X-Session-Token": alice_token})
    assert alice_feed.status_code == 200
    alice_rows = list(alice_feed.json() or [])
    assert alice_rows
    alice_types = {str(r.get("event_type") or "") for r in alice_rows}
    assert "your_video_rated" in alice_types
