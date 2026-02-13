import pytest


pytestmark = pytest.mark.anyio


@pytest.mark.integration
async def test_ai_plan_returns_draft_path_and_courses(app_client):
    # Bootstrap admin login (fresh DB in CI runs).
    login = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert login.status_code == 200
    token = login.json()["token"]

    resp = await app_client.post("/ai/plan", headers={"X-Session-Token": token}, json={"goal": "build an API"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["goal"]
    assert isinstance(body["path"], dict)
    assert isinstance(body["courses"], list)
    assert body["path"]["name"]
    assert len(body["courses"]) >= 1
    assert body["courses"][0]["title"]


@pytest.mark.integration
async def test_ai_plan_requires_goal(app_client):
    login = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = login.json()["token"]

    resp = await app_client.post("/ai/plan", headers={"X-Session-Token": token}, json={"goal": ""})
    assert resp.status_code == 400
