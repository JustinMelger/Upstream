import pytest


pytestmark = pytest.mark.anyio


async def _login_admin(app_client):
    response = await app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["token"]


async def _create_course(app_client, token, title):
    response = await app_client.post(
        "/courses",
        json={"title": title, "description": f"desc: {title}"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 200
    return response.json()["id"]


async def _create_video(app_client, token, title):
    response = await app_client.post(
        "/videos",
        json={
            "title": title,
            "description": f"desc: {title}",
            "provider": "YouTube",
            "category": "Data",
            "url": f"https://www.youtube.com/watch?v={title.lower().replace(' ', '-')}",
        },
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 200
    return response.json()["id"]


async def _create_article(app_client, token, title):
    response = await app_client.post(
        "/articles",
        json={"title": title, "url": f"https://example.com/{title.lower().replace(' ', '-')}"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 200
    return response.json()["id"]


async def _create_user(app_client, token, username, role="user"):
    return await app_client.post(
        "/auth/users",
        json={"username": username, "password": "pass123", "role": role},
        headers={"X-Session-Token": token},
    )


@pytest.mark.integration
async def test_paths_requires_auth(app_client):
    """Path listing requires authentication."""
    response = await app_client.get("/paths")
    assert response.status_code == 401


@pytest.mark.integration
async def test_list_paths_empty(app_client):
    """Listing paths returns a list payload for authenticated users."""
    token = await _login_admin(app_client)
    response = await app_client.get("/paths", headers={"X-Session-Token": token})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.integration
async def test_create_path_missing_name(app_client):
    """Creating a path without a name returns 400."""
    token = await _login_admin(app_client)
    response = await app_client.post("/paths", json={"name": ""}, headers={"X-Session-Token": token})
    assert response.status_code == 400
    body = response.json()
    assert body.get("status") == "error"
    assert body.get("message") == "missing_name"
    assert "timestamp" in body


@pytest.mark.integration
async def test_path_lifecycle_and_selection(app_client):
    """Users can create paths, and users can select/unselect them."""
    token = await _login_admin(app_client)
    await _create_user(app_client, token, "alice", role="user")
    alice_login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    alice_token = alice_login.json()["token"]
    course_id = await _create_course(app_client, token, "Path Course 1")
    create = await app_client.post(
        "/paths",
        json={"name": "Data Path", "description": "Learn data", "items": [{"type": "course", "id": course_id, "position": 0}]},
        headers={"X-Session-Token": alice_token},
    )
    assert create.status_code == 200
    path_id = create.json()["id"]

    select = await app_client.post(f"/paths/{path_id}/select", headers={"X-Session-Token": token})
    assert select.status_code == 200
    assert select.json()["path_id"] == str(path_id)

    selected_after_select = await app_client.get("/paths/selected/list", headers={"X-Session-Token": token})
    assert selected_after_select.status_code == 200
    selected_match = [item for item in selected_after_select.json() if item["id"] == path_id]
    assert selected_match and selected_match[0]["status"] == "interested"

    status = await app_client.post(
        f"/paths/{path_id}/status",
        json={"status": "in_progress"},
        headers={"X-Session-Token": token},
    )
    assert status.status_code == 200
    assert status.json()["updated"] == 1

    selected = await app_client.get("/paths/selected/list", headers={"X-Session-Token": token})
    assert selected.status_code == 200
    match = [item for item in selected.json() if item["id"] == path_id]
    assert match and match[0]["status"] == "in_progress"

    unselect = await app_client.post(f"/paths/{path_id}/unselect", headers={"X-Session-Token": token})
    assert unselect.status_code == 200
    assert unselect.json()["removed"] == 1

    delete = await app_client.delete(f"/paths/{path_id}", headers={"X-Session-Token": alice_token})
    assert delete.status_code == 200
    assert delete.json()["deleted"] is True


@pytest.mark.integration
async def test_create_path_with_mixed_learning_items_returns_items_only(app_client):
    """Mixed path payloads return typed items only."""
    token = await _login_admin(app_client)
    course_id = await _create_course(app_client, token, "Mixed Path Course")
    video_id = await _create_video(app_client, token, "Mixed Path Video")
    article_id = await _create_article(app_client, token, "Mixed Path Article")

    create = await app_client.post(
        "/paths",
        json={
            "name": "Mixed Learning Path",
            "description": "Learn in mixed media",
            "items": [
                {"type": "video", "id": video_id, "position": 0},
                {"type": "course", "id": course_id, "position": 1},
                {"type": "article", "id": article_id, "position": 2},
            ],
        },
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 200
    payload = create.json()
    assert [item["type"] for item in payload["items"]] == ["video", "course", "article"]
    assert [int(item["id"]) for item in payload["items"]] == [video_id, course_id, article_id]

    detail = await app_client.get(f"/paths/{int(payload['id'])}", headers={"X-Session-Token": token})
    assert detail.status_code == 200
    assert [item["type"] for item in detail.json()["items"]] == ["video", "course", "article"]


@pytest.mark.integration
async def test_create_path_rejects_duplicate_learning_item_refs(app_client):
    token = await _login_admin(app_client)
    course_id = await _create_course(app_client, token, "Duplicate Ref Course")

    create = await app_client.post(
        "/paths",
        json={
            "name": "Duplicate Ref Path",
            "items": [
                {"type": "course", "id": course_id, "position": 0},
                {"type": "course", "id": course_id, "position": 1},
            ],
        },
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 400
    assert create.json().get("message") == "duplicate_item_refs"


@pytest.mark.integration
async def test_select_path_is_idempotent_and_keeps_interested_status(app_client):
    """Selecting the same path multiple times keeps one selected row with interested status."""
    token = await _login_admin(app_client)
    course_id = await _create_course(app_client, token, "Idempotent Selection Course")
    create = await app_client.post(
        "/paths",
        json={
            "name": "Idempotent Selection Path",
            "description": "desc",
            "items": [{"type": "course", "id": course_id, "position": 0}],
        },
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 200
    path_id = int(create.json()["id"])

    first = await app_client.post(f"/paths/{path_id}/select", headers={"X-Session-Token": token})
    assert first.status_code == 200
    second = await app_client.post(f"/paths/{path_id}/select", headers={"X-Session-Token": token})
    assert second.status_code == 200

    selected = await app_client.get("/paths/selected/list", headers={"X-Session-Token": token})
    assert selected.status_code == 200
    rows = [item for item in selected.json() if int(item.get("id") or 0) == path_id]
    assert len(rows) == 1
    assert rows[0]["status"] == "interested"


@pytest.mark.integration
async def test_select_missing_path_returns_not_found(app_client):
    """Selecting a non-existent path returns 404 with standard error payload."""
    token = await _login_admin(app_client)
    response = await app_client.post("/paths/999999/select", headers={"X-Session-Token": token})
    assert response.status_code == 404
    body = response.json()
    assert body.get("status") == "error"
    assert body.get("message") == "not_found"


@pytest.mark.integration
async def test_reselect_path_preserves_existing_selected_status(app_client):
    """Re-selecting a selected path must not overwrite an explicit path status."""
    token = await _login_admin(app_client)
    course_id = await _create_course(app_client, token, "Reselect Preserve Status Course")
    create = await app_client.post(
        "/paths",
        json={
            "name": "Reselect Preserve Status Path",
            "description": "desc",
            "items": [{"type": "course", "id": course_id, "position": 0}],
        },
        headers={"X-Session-Token": token},
    )
    assert create.status_code == 200
    path_id = int(create.json()["id"])

    first = await app_client.post(f"/paths/{path_id}/select", headers={"X-Session-Token": token})
    assert first.status_code == 200

    set_status = await app_client.post(
        f"/paths/{path_id}/status",
        json={"status": "completed"},
        headers={"X-Session-Token": token},
    )
    assert set_status.status_code == 200

    second = await app_client.post(f"/paths/{path_id}/select", headers={"X-Session-Token": token})
    assert second.status_code == 200

    selected = await app_client.get("/paths/selected/list", headers={"X-Session-Token": token})
    assert selected.status_code == 200
    rows = [item for item in selected.json() if int(item.get("id") or 0) == path_id]
    assert len(rows) == 1
    assert rows[0]["status"] == "completed"


@pytest.mark.integration
async def test_path_update_requires_owner_or_admin(app_client):
    """Non-admin users can only update paths they created."""
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    await _create_user(app_client, admin_token, "bob", role="user")

    alice_login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    bob_login = await app_client.post("/auth/login", json={"username": "bob", "password": "pass123"})
    alice_token = alice_login.json()["token"]
    bob_token = bob_login.json()["token"]

    course_id = await _create_course(app_client, admin_token, "P1")
    created = await app_client.post(
        "/paths",
        json={"name": "Owned Path", "description": "", "items": [{"type": "course", "id": course_id, "position": 0}]},
        headers={"X-Session-Token": alice_token},
    )
    assert created.status_code == 200
    path_id = created.json()["id"]

    forbidden = await app_client.put(
        f"/paths/{path_id}",
        json={"name": "Owned Path", "description": "changed", "items": [{"type": "course", "id": course_id, "position": 0}]},
        headers={"X-Session-Token": bob_token},
    )
    assert forbidden.status_code == 403

    ok = await app_client.put(
        f"/paths/{path_id}",
        json={"name": "Owned Path", "description": "changed", "items": [{"type": "course", "id": course_id, "position": 0}]},
        headers={"X-Session-Token": alice_token},
    )
    assert ok.status_code == 200
    assert ok.json()["description"] == "changed"


@pytest.mark.integration
async def test_update_path_rejects_duplicate_learning_item_refs(app_client):
    token = await _login_admin(app_client)
    course_id = await _create_course(app_client, token, "Duplicate Update Course")
    created = await app_client.post(
        "/paths",
        json={"name": "Duplicate Update Path", "items": [{"type": "course", "id": course_id, "position": 0}]},
        headers={"X-Session-Token": token},
    )
    assert created.status_code == 200
    path_id = int(created.json()["id"])

    update = await app_client.put(
        f"/paths/{path_id}",
        json={
            "name": "Duplicate Update Path",
            "items": [
                {"type": "course", "id": course_id, "position": 0},
                {"type": "course", "id": course_id, "position": 1},
            ],
        },
        headers={"X-Session-Token": token},
    )
    assert update.status_code == 400
    assert update.json().get("message") == "duplicate_item_refs"


@pytest.mark.integration
async def test_get_path_not_found_returns_404(app_client):
    """Missing paths return 404."""
    token = await _login_admin(app_client)
    response = await app_client.get("/paths/999999", headers={"X-Session-Token": token})
    assert response.status_code == 404
    body = response.json()
    assert body.get("status") == "error"
    assert body.get("message") == "not_found"


@pytest.mark.integration
async def test_path_review_lifecycle_and_moderation(app_client):
    """Users can review paths; owners/admin can moderate deletes."""
    admin_token = await _login_admin(app_client)
    await _create_user(app_client, admin_token, "alice", role="user")
    await _create_user(app_client, admin_token, "bob", role="user")

    alice_login = await app_client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    bob_login = await app_client.post("/auth/login", json={"username": "bob", "password": "pass123"})
    alice_token = alice_login.json()["token"]
    bob_token = bob_login.json()["token"]

    course_id = await _create_course(app_client, admin_token, "Path Review Course")
    create_path = await app_client.post(
        "/paths",
        json={"name": "Reviewed Path", "description": "desc", "items": [{"type": "course", "id": course_id, "position": 0}]},
        headers={"X-Session-Token": alice_token},
    )
    assert create_path.status_code == 200
    path_id = int(create_path.json()["id"])

    created = await app_client.post(
        f"/paths/{path_id}/reviews",
        json={"rating": 4, "text": "Good structure"},
        headers={"X-Session-Token": alice_token},
    )
    assert created.status_code == 200
    review_id = int(created.json()["id"])
    assert created.json()["created_by"] == "alice"

    # Upsert same reviewer.
    updated = await app_client.post(
        f"/paths/{path_id}/reviews",
        json={"rating": 5, "text": "Even better after update"},
        headers={"X-Session-Token": alice_token},
    )
    assert updated.status_code == 200
    assert int(updated.json()["id"]) == review_id
    assert int(updated.json()["rating"]) == 5

    listing = await app_client.get(f"/paths/{path_id}/reviews", headers={"X-Session-Token": bob_token})
    assert listing.status_code == 200
    rows = listing.json()
    assert rows and int(rows[0]["id"]) == review_id

    summary = await app_client.get(
        "/paths/reviews/summary",
        params={"path_ids": [path_id]},
        headers={"X-Session-Token": bob_token},
    )
    assert summary.status_code == 200
    srows = summary.json()
    assert srows and int(srows[0]["path_id"]) == path_id
    assert int(srows[0]["review_count"]) == 1

    forbidden = await app_client.delete(
        f"/paths/{path_id}/reviews/{review_id}",
        headers={"X-Session-Token": bob_token},
    )
    assert forbidden.status_code == 403

    deleted = await app_client.delete(
        f"/paths/{path_id}/reviews/{review_id}",
        headers={"X-Session-Token": admin_token},
    )
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
