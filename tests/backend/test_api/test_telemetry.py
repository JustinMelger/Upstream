import pytest


pytestmark = pytest.mark.anyio


@pytest.mark.integration
async def test_telemetry_events_are_disabled_by_default(app_client):
    response = await app_client.post(
        "/telemetry/events",
        json={"event_name": "nav_click", "context": {"target": "/home"}},
    )
    assert response.status_code == 404
