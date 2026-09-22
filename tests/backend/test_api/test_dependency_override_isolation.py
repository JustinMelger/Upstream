from __future__ import annotations

from fastapi import HTTPException
from httpx import AsyncClient
import pytest

from backend.api.deps import get_courses_service


pytestmark = pytest.mark.anyio


class _OverrideCoursesService:
    async def get_course_by_id(self, course_id: int) -> dict:
        raise HTTPException(status_code=418, detail="override_active")


async def _login_admin(app_client: AsyncClient) -> str:
    response = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return str(response.json()["token"])


@pytest.mark.integration
async def test_dependency_override_can_be_set_without_local_cleanup(app_client):
    """Intentionally leave an override behind; fixture teardown must clean it."""
    app = app_client.app

    async def _override_courses_service() -> _OverrideCoursesService:
        return _OverrideCoursesService()

    app.dependency_overrides[get_courses_service] = _override_courses_service

    token = await _login_admin(app_client)
    response = await app_client.get("/courses/1", headers={"X-Session-Token": token})
    assert response.status_code == 418
    body = response.json()
    assert body.get("message") == "override_active"


@pytest.mark.integration
async def test_dependency_overrides_are_reset_between_app_client_tests(app_client):
    """The previous test's leaked override must not affect this test."""
    token = await _login_admin(app_client)
    response = await app_client.get("/courses/999999", headers={"X-Session-Token": token})
    assert response.status_code == 404
    assert response.json()["message"] == "not_found"
