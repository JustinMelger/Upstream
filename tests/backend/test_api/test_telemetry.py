import pytest


pytestmark = pytest.mark.anyio


async def _login_admin(app_client):
    response = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["token"]


@pytest.mark.integration
async def test_telemetry_events_requires_auth(app_client):
    response = await app_client.post(
        "/telemetry/events",
        json={"event_name": "nav_click", "context": {"target": "/home"}},
    )
    assert response.status_code == 401


@pytest.mark.integration
async def test_telemetry_events_accepts_valid_payload(app_client):
    token = await _login_admin(app_client)
    response = await app_client.post(
        "/telemetry/events",
        json={"event_name": "nav_click", "context": {"target": "/home"}},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
