import pytest


@pytest.mark.integration
def test_auth_login_rejects_non_string_username(app_client):
    """Auth login request validation rejects invalid field types."""
    response = app_client.post("/auth/login", json={"username": 123, "password": "admin"})
    assert response.status_code == 422


@pytest.mark.integration
def test_courses_create_rejects_non_string_title(app_client):
    """Course create validation rejects invalid field types."""
    login = app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = login.json()["token"]
    response = app_client.post("/courses", json={"title": 123}, headers={"X-Session-Token": token})
    assert response.status_code == 422


@pytest.mark.integration
def test_paths_create_rejects_non_int_course_ids(app_client):
    """Path create validation rejects invalid course_ids element types."""
    login = app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = login.json()["token"]
    response = app_client.post(
        "/paths",
        json={"name": "Bad Path", "course_ids": ["abc"]},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 422


@pytest.mark.integration
def test_tracking_set_rejects_non_string_status(app_client):
    """Tracking validation rejects invalid status type."""
    login = app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = login.json()["token"]

    create_course = app_client.post("/courses", json={"title": "T1"}, headers={"X-Session-Token": token})
    course_id = create_course.json()["id"]

    response = app_client.post(
        "/tracking",
        json={"course_id": course_id, "status": 123},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 422
