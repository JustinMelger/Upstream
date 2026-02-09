import pytest

import backend.main as main


pytestmark = pytest.mark.anyio


@pytest.mark.integration
async def test_health_endpoint(app_client):
    """Main app exposes the health endpoint."""
    response = await app_client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"
