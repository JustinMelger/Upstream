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
