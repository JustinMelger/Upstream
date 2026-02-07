import pytest

from backend.api.deps import get_courses_service
from backend.services.courses_service import CoursesService


def _login_admin(app_client) -> str:
    response = app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["token"]


@pytest.mark.integration
def test_service_error_returns_standard_envelope_for_409_duplicate_path_name(app_client):
    """Duplicate path names return a domain error envelope with status/message/timestamp."""
    token = _login_admin(app_client)

    first = app_client.post("/paths", json={"name": "Duplicate", "course_ids": []}, headers={"X-Session-Token": token})
    assert first.status_code == 200

    second = app_client.post("/paths", json={"name": "Duplicate", "course_ids": []}, headers={"X-Session-Token": token})
    assert second.status_code == 409
    body = second.json()
    assert body.get("status") == "error"
    assert body.get("message") == "duplicate_name"
    assert "timestamp" in body


@pytest.mark.integration
def test_service_error_returns_standard_envelope_for_400_invalid_tracking_status(app_client):
    """Invalid tracking statuses return a 400 domain error envelope."""
    token = _login_admin(app_client)

    create_course = app_client.post("/courses", json={"title": "Tracking Course"}, headers={"X-Session-Token": token})
    assert create_course.status_code == 200
    course_id = create_course.json()["id"]

    response = app_client.post(
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
def test_http_exception_is_not_wrapped_in_service_error_envelope(app_client):
    """Auth/permission HTTPExceptions keep the default FastAPI error shape."""
    unauth = app_client.get("/courses")
    assert unauth.status_code == 401
    assert "detail" in unauth.json()
    assert "status" not in unauth.json()

    admin_token = _login_admin(app_client)
    create_user = app_client.post(
        "/auth/users",
        json={"username": "student2", "password": "pass123", "role": "user"},
        headers={"X-Session-Token": admin_token},
    )
    assert create_user.status_code in (200, 409)

    user_login = app_client.post("/auth/login", json={"username": "student2", "password": "pass123"})
    assert user_login.status_code == 200
    user_token = user_login.json()["token"]

    forbidden = app_client.post(
        "/courses",
        json={"title": "Intro"},
        headers={"X-Session-Token": user_token},
    )
    assert forbidden.status_code == 403
    assert forbidden.json().get("detail") == "admin_required"
    assert "status" not in forbidden.json()


@pytest.mark.integration
def test_unexpected_exception_is_converted_to_500_service_error_envelope(app_client):
    """Uncaught exceptions in a service return a 500 domain error envelope."""

    class FailingCoursesRepo:
        def list_courses(self, **_kwargs):
            raise Exception("boom")

        def get_course_by_id(self, course_id: int):  # pragma: no cover
            raise AssertionError("not used")

        def create_course(self, **_kwargs):  # pragma: no cover
            raise AssertionError("not used")

        def update_course(self, **_kwargs):  # pragma: no cover
            raise AssertionError("not used")

        def delete_course(self, course_id: int):  # pragma: no cover
            raise AssertionError("not used")

    token = _login_admin(app_client)

    app = app_client.app
    app.dependency_overrides[get_courses_service] = lambda: CoursesService(FailingCoursesRepo())
    try:
        response = app_client.get("/courses", headers={"X-Session-Token": token})
        assert response.status_code == 500
        body = response.json()
        assert body.get("status") == "error"
        assert body.get("message") == "An unexpected error occurred while handling courses"
        assert "timestamp" in body
    finally:
        app.dependency_overrides.pop(get_courses_service, None)
