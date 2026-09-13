"""Authenticated metadata API remains read-only and CSRF protected."""

from unittest.mock import AsyncMock

import pytest

from backend.services import url_preview_service


pytestmark = [pytest.mark.integration, pytest.mark.anyio]


async def test_metadata_authentication_and_csrf(app_client, monkeypatch):
    call = AsyncMock(return_value=("https://example.com", "<title>Resource</title>"))
    monkeypatch.setattr(url_preview_service, "fetch_html", call)
    payload = {"url": "https://example.com/auth-test"}
    assert (await app_client.post("/url-preview/metadata", json=payload)).status_code == 401
    login = await app_client.post(
        "/auth/browser/login", headers={"Origin": "http://localhost:8080"}, json={"username": "admin", "password": "admin"}
    )
    assert login.status_code == 200
    assert (await app_client.post("/url-preview/metadata", json=payload)).status_code == 403
    headers = {"Origin": "http://localhost:8080", "X-CSRF-Token": login.json()["csrf_token"]}
    response = await app_client.post("/url-preview/metadata", json=payload, headers=headers)
    assert response.status_code == 200 and response.json()["title"] == "Resource"
    assert (
        await app_client.post("/url-preview/metadata", json=payload, headers=headers | {"Origin": "https://evil.example"})
    ).status_code == 403
    assert call.await_count == 1
