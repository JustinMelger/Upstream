import pytest


def _login_admin(app_client):
    response = app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["token"]


def _create_course(app_client, token, title):
    response = app_client.post(
        "/courses",
        json={"title": title},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 200
    return response.json()["id"]


@pytest.mark.integration
def test_paths_requires_auth(app_client):
    """Path listing requires authentication."""
    response = app_client.get("/paths")
    assert response.status_code == 401


@pytest.mark.integration
def test_list_paths_empty(app_client):
    """Listing paths returns a list payload for authenticated users."""
    token = _login_admin(app_client)
    response = app_client.get("/paths", headers={"X-Session-Token": token})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.integration
def test_create_path_missing_name(app_client):
    """Creating a path without a name returns 400."""
    token = _login_admin(app_client)
    response = app_client.post("/paths", json={"name": ""}, headers={"X-Session-Token": token})
    assert response.status_code == 400
    assert response.json().get("detail") == "missing_name"


@pytest.mark.integration
def test_path_lifecycle_and_selection(app_client):
    """Admins can manage paths, and users can select/unselect them."""
    token = _login_admin(app_client)
    course_id = _create_course(app_client, token, "Path Course 1")
    create = app_client.post(
        "/paths",
        json={"name": "Data Path", "description": "Learn data", "course_ids": [course_id]},
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 200
    path_id = create.json()["id"]

    select = app_client.post(f"/paths/{path_id}/select", headers={"X-Session-Token": token})
    assert select.status_code == 200
    assert select.json()["path_id"] == str(path_id)

    status = app_client.post(
        f"/paths/{path_id}/status",
        json={"status": "in_progress"},
        headers={"X-Session-Token": token},
    )
    assert status.status_code == 200
    assert status.json()["updated"] == 1

    selected = app_client.get("/paths/selected/list", headers={"X-Session-Token": token})
    assert selected.status_code == 200
    match = [item for item in selected.json() if item["id"] == path_id]
    assert match and match[0]["status"] == "in_progress"

    unselect = app_client.post(f"/paths/{path_id}/unselect", headers={"X-Session-Token": token})
    assert unselect.status_code == 200
    assert unselect.json()["removed"] == 1

    delete = app_client.delete(f"/paths/{path_id}", headers={"X-Session-Token": token})
    assert delete.status_code == 200
    assert delete.json()["deleted"] is True
