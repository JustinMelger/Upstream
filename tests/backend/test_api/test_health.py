import pytest


pytestmark = pytest.mark.anyio


@pytest.mark.integration
async def test_health(app_client):
    """Health endpoint responds with ok status."""
    response = await app_client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"
