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


async def _create_path(app_client, token, name: str):
    created = await app_client.post(
        "/paths",
        json={"name": name, "description": "desc", "course_ids": []},
        headers={"X-Session-Token": token},
    )
    assert created.status_code == 200
    return int(created.json()["id"])


@pytest.mark.integration
async def test_path_reviews_requires_auth(app_client):
    response = await app_client.get("/paths/1/reviews")
    assert response.status_code == 401


@pytest.mark.integration
async def test_path_reviews_create_and_list(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice_pr", role="user")

    login = await app_client.post("/auth/login", json={"username": "alice_pr", "password": "pass123"})
    token = login.json()["token"]
    path_id = await _create_path(app_client, token, "Reviewable Path")

    create_review = await app_client.post(
        f"/paths/{path_id}/reviews",
        json={"rating": 5, "text": "Great path"},
        headers={"X-Session-Token": token},
    )
    assert create_review.status_code == 200
    review = create_review.json()
    assert review["path_id"] == path_id
    assert review["rating"] == 5
    assert review["created_by"] == "alice_pr"

    update_review = await app_client.post(
        f"/paths/{path_id}/reviews",
        json={"rating": 4, "text": "Updated path review"},
        headers={"X-Session-Token": token},
    )
    assert update_review.status_code == 200
    assert update_review.json()["id"] == review["id"]
    assert update_review.json()["rating"] == 4

    listing = await app_client.get(f"/paths/{path_id}/reviews", headers={"X-Session-Token": token})
    assert listing.status_code == 200
    rows = listing.json()
    assert len([r for r in rows if r.get("id") == review["id"]]) == 1
    updated = [r for r in rows if r.get("id") == review["id"]][0]
    assert updated["rating"] == 4


@pytest.mark.integration
async def test_path_reviews_delete_permissions(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice_pr2", role="user")
    await _create_user(app_client, admin_token, "bob_pr2", role="user")

    login_alice = await app_client.post("/auth/login", json={"username": "alice_pr2", "password": "pass123"})
    token_alice = login_alice.json()["token"]
    login_bob = await app_client.post("/auth/login", json={"username": "bob_pr2", "password": "pass123"})
    token_bob = login_bob.json()["token"]

    path_id = await _create_path(app_client, token_alice, "Delete Path Review")
    create_review = await app_client.post(
        f"/paths/{path_id}/reviews",
        json={"rating": 5, "text": "ok"},
        headers={"X-Session-Token": token_alice},
    )
    assert create_review.status_code == 200
    review_id = create_review.json()["id"]

    forbidden = await app_client.delete(
        f"/paths/{path_id}/reviews/{review_id}",
        headers={"X-Session-Token": token_bob},
    )
    assert forbidden.status_code == 403

    deleted = await app_client.delete(
        f"/paths/{path_id}/reviews/{review_id}",
        headers={"X-Session-Token": token_alice},
    )
    assert deleted.status_code == 200
    assert deleted.json().get("deleted") is True

    listing = await app_client.get(f"/paths/{path_id}/reviews", headers={"X-Session-Token": token_alice})
    assert listing.status_code == 200
    assert all(r.get("id") != review_id for r in listing.json())


@pytest.mark.integration
async def test_path_reviews_summary_endpoint(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice_pr3", role="user")
    await _create_user(app_client, admin_token, "bob_pr3", role="user")

    login_alice = await app_client.post("/auth/login", json={"username": "alice_pr3", "password": "pass123"})
    token_alice = login_alice.json()["token"]
    login_bob = await app_client.post("/auth/login", json={"username": "bob_pr3", "password": "pass123"})
    token_bob = login_bob.json()["token"]

    id1 = await _create_path(app_client, token_alice, "Summary Path 1")
    id2 = await _create_path(app_client, token_alice, "Summary Path 2")

    await app_client.post(
        f"/paths/{id1}/reviews",
        json={"rating": 4, "text": ""},
        headers={"X-Session-Token": token_alice},
    )
    await app_client.post(
        f"/paths/{id1}/reviews",
        json={"rating": 2, "text": ""},
        headers={"X-Session-Token": token_bob},
    )
    await app_client.post(
        f"/paths/{id2}/reviews",
        json={"rating": 5, "text": ""},
        headers={"X-Session-Token": token_bob},
    )

    summary = await app_client.get(
        "/paths/reviews/summary",
        params=[("path_ids", id1), ("path_ids", id2)],
        headers={"X-Session-Token": token_alice},
    )
    assert summary.status_code == 200
    rows = summary.json()
    by_id = {r.get("path_id"): r for r in rows}
    assert by_id[id1]["review_count"] == 2
    assert by_id[id2]["review_count"] == 1
