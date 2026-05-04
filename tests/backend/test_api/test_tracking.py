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


async def _create_user(app_client, token, username: str, role: str = "user") -> None:
    response = await app_client.post(
        "/auth/users",
        json={"username": username, "password": "pass123", "role": role},
        headers={"X-Session-Token": token},
    )
    assert response.status_code in (200, 409)


async def _login(app_client, username: str, password: str) -> str:
    response = await app_client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return str(response.json()["token"])


async def _create_team(app_client, token: str, name: str) -> int:
    response = await app_client.post(
        "/teams",
        json={"name": name, "description": ""},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 200
    return int(response.json()["id"])


async def _add_team_member(app_client, token: str, team_id: int, username: str) -> None:
    response = await app_client.post(
        f"/teams/{team_id}/members",
        json={"user_id": username, "role": "member"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 200


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
    """Tracking team stats are available to authenticated users."""
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
    assert response.status_code == 200

    by_user = await app_client.get("/tracking/stats/users", headers={"X-Session-Token": user_token})
    assert by_user.status_code == 200

    admin_stats = await app_client.get("/tracking/stats", headers={"X-Session-Token": admin_token})
    assert admin_stats.status_code == 200


@pytest.mark.integration
async def test_tracking_team_totals_merge_all_memberships_for_current_user(app_client):
    """Team totals should use the union of all members across the viewer's teams."""
    admin_token = await _login_admin(app_client)
    for username in ("alice", "bob", "charlie"):
        await _create_user(app_client, admin_token, username)

    alice_token = await _login(app_client, "alice", "pass123")
    bob_token = await _login(app_client, "bob", "pass123")
    charlie_token = await _login(app_client, "charlie", "pass123")

    data_team_id = await _create_team(app_client, alice_token, "Data Team")
    video_team_id = await _create_team(app_client, bob_token, "Video Team")
    await _add_team_member(app_client, alice_token, data_team_id, "bob")
    await _add_team_member(app_client, bob_token, video_team_id, "alice")
    await _add_team_member(app_client, bob_token, video_team_id, "charlie")

    alice_course_id = await _create_course(app_client, alice_token, "Alice Course")
    bob_course_id = await _create_course(app_client, bob_token, "Bob Course")
    charlie_course_id = await _create_course(app_client, charlie_token, "Charlie Course")

    for token, course_id, status in (
        (alice_token, alice_course_id, "completed"),
        (bob_token, bob_course_id, "in_progress"),
        (charlie_token, charlie_course_id, "interested"),
    ):
        response = await app_client.post(
            "/tracking",
            json={"course_id": course_id, "status": status},
            headers={"X-Session-Token": token},
        )
        assert response.status_code == 200

    stats_response = await app_client.get("/tracking/stats", headers={"X-Session-Token": alice_token})
    assert stats_response.status_code == 200
    assert stats_response.json() == {"interested": 1, "in_progress": 1, "completed": 1}

    by_user_response = await app_client.get("/tracking/stats/users", headers={"X-Session-Token": alice_token})
    assert by_user_response.status_code == 200
    assert by_user_response.json() == [
        {"colleague_id": "alice", "interested": 0, "in_progress": 0, "completed": 1},
        {"colleague_id": "bob", "interested": 0, "in_progress": 1, "completed": 0},
        {"colleague_id": "charlie", "interested": 1, "in_progress": 0, "completed": 0},
    ]
