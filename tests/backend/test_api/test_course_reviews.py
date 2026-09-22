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
async def test_course_reviews_requires_auth(app_client):
    response = await app_client.get("/courses/1/reviews")
    assert response.status_code == 401


@pytest.mark.integration
async def test_course_reviews_create_and_list(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")

    login = await app_client.post("/auth/login", json={"username": "alice", "password": "test-password-123"})
    token = login.json()["token"]

    created_course = await app_client.post(
        "/courses",
        json={"title": "Review Me", "description": "desc"},
        headers={"X-Session-Token": token},
    )
    assert created_course.status_code == 200
    course_id = created_course.json()["id"]

    create_review = await app_client.post(
        f"/courses/{course_id}/reviews",
        json={"rating": 5, "text": "Great course"},
        headers={"X-Session-Token": token},
    )
    assert create_review.status_code == 200
    review = create_review.json()
    assert review["course_id"] == course_id
    assert review["rating"] == 5
    assert review["created_by"] == "alice"

    update_review = await app_client.post(
        f"/courses/{course_id}/reviews",
        json={"rating": 4, "text": "Updated review"},
        headers={"X-Session-Token": token},
    )
    assert update_review.status_code == 200
    assert update_review.json()["id"] == review["id"]
    assert update_review.json()["rating"] == 4

    listing = await app_client.get(f"/courses/{course_id}/reviews", headers={"X-Session-Token": token})
    assert listing.status_code == 200
    rows = listing.json()
    assert len([r for r in rows if r.get("id") == review["id"]]) == 1
    updated = [r for r in rows if r.get("id") == review["id"]][0]
    assert updated["rating"] == 4


@pytest.mark.integration
async def test_course_reviews_reject_invalid_rating(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice2", role="user")
    login = await app_client.post("/auth/login", json={"username": "alice2", "password": "test-password-123"})
    token = login.json()["token"]

    created_course = await app_client.post(
        "/courses",
        json={"title": "Review Me 2", "description": "desc"},
        headers={"X-Session-Token": token},
    )
    course_id = created_course.json()["id"]

    bad = await app_client.post(
        f"/courses/{course_id}/reviews",
        json={"rating": 6, "text": "nope"},
        headers={"X-Session-Token": token},
    )
    assert bad.status_code == 422 or bad.status_code == 400


@pytest.mark.integration
async def test_course_reviews_delete_permissions(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice3", role="user")
    await _create_user(app_client, admin_token, "bob3", role="user")

    login_alice = await app_client.post("/auth/login", json={"username": "alice3", "password": "test-password-123"})
    token_alice = login_alice.json()["token"]
    login_bob = await app_client.post("/auth/login", json={"username": "bob3", "password": "test-password-123"})
    token_bob = login_bob.json()["token"]

    created_course = await app_client.post(
        "/courses",
        json={"title": "Delete Review", "description": "desc"},
        headers={"X-Session-Token": token_alice},
    )
    assert created_course.status_code == 200
    course_id = created_course.json()["id"]

    create_review = await app_client.post(
        f"/courses/{course_id}/reviews",
        json={"rating": 5, "text": "ok"},
        headers={"X-Session-Token": token_alice},
    )
    assert create_review.status_code == 200
    review_id = create_review.json()["id"]

    forbidden = await app_client.delete(
        f"/courses/{course_id}/reviews/{review_id}",
        headers={"X-Session-Token": token_bob},
    )
    assert forbidden.status_code == 403

    deleted = await app_client.delete(
        f"/courses/{course_id}/reviews/{review_id}",
        headers={"X-Session-Token": token_alice},
    )
    assert deleted.status_code == 200
    assert deleted.json().get("deleted") is True

    listing = await app_client.get(f"/courses/{course_id}/reviews", headers={"X-Session-Token": token_alice})
    assert listing.status_code == 200
    assert all(r.get("id") != review_id for r in listing.json())


@pytest.mark.integration
async def test_course_reviews_summary_endpoint(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice4", role="user")
    await _create_user(app_client, admin_token, "bob4", role="user")

    login_alice = await app_client.post("/auth/login", json={"username": "alice4", "password": "test-password-123"})
    token_alice = login_alice.json()["token"]
    login_bob = await app_client.post("/auth/login", json={"username": "bob4", "password": "test-password-123"})
    token_bob = login_bob.json()["token"]

    c1 = await app_client.post(
        "/courses",
        json={"title": "Summary 1", "description": "desc"},
        headers={"X-Session-Token": token_alice},
    )
    c2 = await app_client.post(
        "/courses",
        json={"title": "Summary 2", "description": "desc"},
        headers={"X-Session-Token": token_alice},
    )
    assert c1.status_code == 200
    assert c2.status_code == 200
    id1 = c1.json()["id"]
    id2 = c2.json()["id"]

    await app_client.post(
        f"/courses/{id1}/reviews",
        json={"rating": 4, "text": ""},
        headers={"X-Session-Token": token_alice},
    )
    await app_client.post(
        f"/courses/{id1}/reviews",
        json={"rating": 2, "text": ""},
        headers={"X-Session-Token": token_bob},
    )
    await app_client.post(
        f"/courses/{id2}/reviews",
        json={"rating": 5, "text": ""},
        headers={"X-Session-Token": token_bob},
    )

    catalog = await app_client.get("/catalog?type=course", headers={"X-Session-Token": token_alice})
    assert catalog.status_code == 200
    by_id = {row["id"]: row for row in catalog.json()["items"]}
    assert by_id[id1]["review_count"] == 2
    assert by_id[id2]["review_count"] == 1
    assert by_id[id1]["rating"] == 3
    assert by_id[id2]["rating"] == 5
