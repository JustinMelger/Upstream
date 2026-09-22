import pytest

from backend.api.deps import get_courses_service
from backend.services.courses_service import CoursesService


pytestmark = pytest.mark.anyio


async def _login_admin(app_client) -> str:
    response = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["token"]


@pytest.mark.integration
async def test_service_error_returns_standard_envelope_for_409_duplicate_path_name(app_client):
    """Duplicate path names return a domain error envelope with status/message/timestamp."""
    token = await _login_admin(app_client)

    first = await app_client.post("/paths", json={"name": "Duplicate", "items": []}, headers={"X-Session-Token": token})
    assert first.status_code == 200

    second = await app_client.post("/paths", json={"name": "Duplicate", "items": []}, headers={"X-Session-Token": token})
    assert second.status_code == 409
    body = second.json()
    assert body.get("status") == "error"
    assert body.get("message") == "duplicate_name"
    assert "timestamp" in body


@pytest.mark.integration
async def test_service_error_returns_standard_envelope_for_400_invalid_tracking_status(app_client):
    """Invalid tracking statuses return a 400 domain error envelope."""
    token = await _login_admin(app_client)

    create_course = await app_client.post(
        "/courses",
        json={"title": "Tracking Course", "description": "desc"},
        headers={"X-Session-Token": token},
    )
    assert create_course.status_code == 200
    course_id = create_course.json()["id"]

    response = await app_client.post(
        "/tracking",
        json={"course_id": course_id, "status": "bad_status"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 400
    body = response.json()
    assert body.get("status") == "error"
    assert body.get("message") == "invalid_status"
    assert "timestamp" in body


@pytest.mark.integration
async def test_http_exception_returns_standard_envelope(app_client):
    """HTTPExceptions return the same standard envelope as domain errors."""
    unauth = await app_client.get("/courses/1")
    assert unauth.status_code == 401
    body = unauth.json()
    assert body.get("status") == "error"
    assert body.get("message") == "unauthorized"
    assert "timestamp" in body

    admin_token = await _login_admin(app_client)
    create_user = await app_client.post(
        "/auth/users",
        json={"username": "student2", "password": "test-password-123", "role": "user"},
        headers={"X-Session-Token": admin_token},
    )
    assert create_user.status_code in (200, 409)

    user_login = await app_client.post("/auth/login", json={"username": "student2", "password": "test-password-123"})
    assert user_login.status_code == 200
    user_token = user_login.json()["token"]

    create_other = await app_client.post(
        "/auth/users",
        json={"username": "student3", "password": "test-password-123", "role": "user"},
        headers={"X-Session-Token": admin_token},
    )
    assert create_other.status_code in (200, 409)
    other_login = await app_client.post("/auth/login", json={"username": "student3", "password": "test-password-123"})
    other_token = other_login.json()["token"]

    owned = await app_client.post(
        "/courses",
        json={"title": "Intro", "description": "desc"},
        headers={"X-Session-Token": user_token},
    )
    assert owned.status_code == 200
    course_id = owned.json()["id"]

    forbidden = await app_client.put(
        f"/courses/{course_id}",
        json={"title": "Hacked", "description": "desc"},
        headers={"X-Session-Token": other_token},
    )
    assert forbidden.status_code == 403
    forbidden_body = forbidden.json()
    assert forbidden_body.get("status") == "error"
    assert forbidden_body.get("message") == "forbidden"
    assert "timestamp" in forbidden_body


@pytest.mark.integration
async def test_unexpected_exception_is_converted_to_500_service_error_envelope(app_client):
    """Uncaught exceptions in a service return a 500 domain error envelope."""

    class FailingCoursesRepo:
        async def get_course_by_id(self, course_id: int):
            raise Exception("boom")

        async def create_course(self, **_kwargs):  # pragma: no cover
            raise AssertionError("not used")

        async def update_course(self, **_kwargs):  # pragma: no cover
            raise AssertionError("not used")

        async def delete_course(self, course_id: int):  # pragma: no cover
            raise AssertionError("not used")

        session = None

    token = await _login_admin(app_client)

    app = app_client.app

    async def _override_courses_service():
        return CoursesService(FailingCoursesRepo())

    app.dependency_overrides[get_courses_service] = _override_courses_service
    try:
        response = await app_client.get("/courses/1", headers={"X-Session-Token": token})
        assert response.status_code == 500
        body = response.json()
        assert body.get("status") == "error"
        assert body.get("message") == "An unexpected error occurred while handling courses"
        assert "timestamp" in body
    finally:
        app.dependency_overrides.pop(get_courses_service, None)
