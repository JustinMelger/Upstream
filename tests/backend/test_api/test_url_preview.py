import pytest


pytestmark = pytest.mark.anyio


async def _login_admin(app_client):
    response = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["token"]


@pytest.mark.integration
async def test_url_preview_metadata_requires_auth(app_client):
    response = await app_client.post("/url-preview/metadata", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert response.status_code == 401


@pytest.mark.integration
async def test_url_preview_metadata_returns_suggestions_for_youtube_url(app_client):
    token = await _login_admin(app_client)
    response = await app_client.post(
        "/url-preview/metadata",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_url"].startswith("https://www.youtube.com/watch")
    assert payload["preview_image_url"].endswith("/dQw4w9WgXcQ/hqdefault.jpg")
    assert isinstance(payload.get("suggested_tags"), list)
