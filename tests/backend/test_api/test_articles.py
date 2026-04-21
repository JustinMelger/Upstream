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
async def test_articles_requires_auth(app_client):
    response = await app_client.get("/articles")
    assert response.status_code == 401


@pytest.mark.integration
async def test_article_create_and_list(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    token = login.json()["token"]

    create = await app_client.post(
        "/articles",
        json={"title": "SQL Bootcamp", "url": "https://example.com/sql", "tags": "sql,data"},
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 200
    payload = create.json()
    assert payload["title"] == "SQL Bootcamp"
    assert payload["created_by"] == "alice"
    assert payload["url"].startswith("https://")

    listing = await app_client.get("/articles", headers={"X-Session-Token": token})
    assert listing.status_code == 200
    rows = listing.json()
    assert any(r.get("id") == payload["id"] for r in rows)


@pytest.mark.integration
async def test_article_create_duplicate_url_returns_409(app_client):
    admin_token = await _login_admin(app_client)
    create = await app_client.post(
        "/articles",
        json={"title": "SQL Bootcamp", "url": "https://example.com/sql", "tags": "sql,data"},
        headers={"X-Session-Token": admin_token},
    )
    assert create.status_code == 200

    duplicate = await app_client.post(
        "/articles",
        json={"title": "Same URL", "url": " https://example.com/sql ", "tags": "other"},
        headers={"X-Session-Token": admin_token},
    )
    assert duplicate.status_code == 409
    body = duplicate.json()
    assert body.get("status") == "error"
    assert body.get("message") == "duplicate_url"


@pytest.mark.integration
async def test_article_review_routes_return_404_for_missing_parent(app_client):
    token = await _login_admin(app_client)

    listing = await app_client.get("/articles/999999/reviews", headers={"X-Session-Token": token})
    assert listing.status_code == 404
    assert listing.json().get("message") == "not_found"

    create = await app_client.post(
        "/articles/999999/reviews",
        json={"rating": 4, "text": "Useful"},
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 404
    assert create.json().get("message") == "not_found"


@pytest.mark.integration
async def test_article_review_lifecycle_and_moderation(app_client):
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    await _create_user(app_client, admin_token, "bob", role="user")

    alice_login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    bob_login = await app_client.post("/auth/login", json={"username": "bob", "password": "pass123"})
    alice_token = alice_login.json()["token"]
    bob_token = bob_login.json()["token"]

    create = await app_client.post(
        "/articles",
        json={"title": "System Design", "url": "https://example.com/design", "tags": "architecture"},
        headers={"X-Session-Token": alice_token},
    )
    assert create.status_code == 200
    article_id = int(create.json()["id"])

    review = await app_client.post(
        f"/articles/{article_id}/reviews",
        json={"rating": 4, "text": "Useful overview"},
        headers={"X-Session-Token": alice_token},
    )
    assert review.status_code == 200
    review_id = int(review.json()["id"])
    assert review.json()["created_by"] == "alice"

    # Upsert same user's review.
    review2 = await app_client.post(
        f"/articles/{article_id}/reviews",
        json={"rating": 5, "text": "Updated"},
        headers={"X-Session-Token": alice_token},
    )
    assert review2.status_code == 200
    assert int(review2.json()["id"]) == review_id
    assert int(review2.json()["rating"]) == 5

    listing = await app_client.get(f"/articles/{article_id}/reviews", headers={"X-Session-Token": bob_token})
    assert listing.status_code == 200
    rows = listing.json()
    assert rows and int(rows[0]["id"]) == review_id

    summary = await app_client.get(
        "/articles/reviews/summary",
        params={"article_ids": [article_id]},
        headers={"X-Session-Token": bob_token},
    )
    assert summary.status_code == 200
    srows = summary.json()
    assert srows and int(srows[0]["article_id"]) == article_id
    assert int(srows[0]["review_count"]) == 1

    # Non-owner non-admin cannot delete.
    forbidden = await app_client.delete(
        f"/articles/{article_id}/reviews/{review_id}",
        headers={"X-Session-Token": bob_token},
    )
    assert forbidden.status_code == 403

    # Admin can moderate-delete.
    deleted = await app_client.delete(
        f"/articles/{article_id}/reviews/{review_id}",
        headers={"X-Session-Token": admin_token},
    )
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
