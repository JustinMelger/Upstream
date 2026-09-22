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
async def test_videos_requires_auth(app_client):
    response = await app_client.get("/catalog?type=video")
    assert response.status_code == 401


@pytest.mark.integration
async def test_video_create_detail_and_catalog(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    login = await app_client.post("/auth/login", json={"username": "alice", "password": "test-password-123"})
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

    listing = await app_client.get("/catalog?type=video", headers={"X-Session-Token": token})
    assert listing.status_code == 200
    rows = listing.json()["items"]
    assert any(int(row.get("id") or 0) == int(payload["id"]) for row in rows)


@pytest.mark.integration
async def test_video_review_routes_return_404_for_missing_parent(app_client):
    token = await _login_admin(app_client)

    listing = await app_client.get("/videos/999999/reviews", headers={"X-Session-Token": token})
    assert listing.status_code == 404
    assert listing.json().get("message") == "not_found"

    create = await app_client.post(
        "/videos/999999/reviews",
        json={"rating": 4, "text": "Useful"},
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 404
    assert create.json().get("message") == "not_found"


@pytest.mark.integration
async def test_video_review_lifecycle_and_moderation(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    await _create_user(app_client, admin_token, "bob", role="user")

    alice_login = await app_client.post("/auth/login", json={"username": "alice", "password": "test-password-123"})
    bob_login = await app_client.post("/auth/login", json={"username": "bob", "password": "test-password-123"})
    alice_token = alice_login.json()["token"]
    bob_token = bob_login.json()["token"]

    create = await app_client.post(
        "/videos",
        json={
            "title": "System Design video",
            "description": "Watch this",
            "provider": "YouTube",
            "category": "Architecture",
            "url": "https://www.youtube.com/watch?v=video-review",
        },
        headers={"X-Session-Token": alice_token},
    )
    assert create.status_code == 200
    video_id = int(create.json()["id"])

    review = await app_client.post(
        f"/videos/{video_id}/reviews",
        json={"rating": 4, "text": "Useful walkthrough"},
        headers={"X-Session-Token": alice_token},
    )
    assert review.status_code == 200
    review_id = int(review.json()["id"])
    assert review.json()["created_by"] == "alice"

    review2 = await app_client.post(
        f"/videos/{video_id}/reviews",
        json={"rating": 5, "text": "Updated"},
        headers={"X-Session-Token": alice_token},
    )
    assert review2.status_code == 200
    assert int(review2.json()["id"]) == review_id
    assert int(review2.json()["rating"]) == 5

    listing = await app_client.get(f"/videos/{video_id}/reviews", headers={"X-Session-Token": bob_token})
    assert listing.status_code == 200
    rows = listing.json()
    assert rows and int(rows[0]["id"]) == review_id

    catalog = await app_client.get("/catalog?type=video", headers={"X-Session-Token": bob_token})
    assert catalog.status_code == 200
    catalog_item = next(item for item in catalog.json()["items"] if int(item["id"]) == video_id)
    assert catalog_item["review_count"] == 1
    assert catalog_item["rating"] == 5

    forbidden = await app_client.delete(
        f"/videos/{video_id}/reviews/{review_id}",
        headers={"X-Session-Token": bob_token},
    )
    assert forbidden.status_code == 403

    deleted = await app_client.delete(
        f"/videos/{video_id}/reviews/{review_id}",
        headers={"X-Session-Token": admin_token},
    )
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
