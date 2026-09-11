"""React release contracts exercised against disposable PostgreSQL."""

import pytest
from sqlalchemy import Engine, event

from backend.api import browser_auth
from backend.core import browser_security
from backend.core.config import Settings


pytestmark = pytest.mark.integration


async def login(client, username="admin", password="admin"):
    response = await client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"X-Session-Token": response.json()["token"]}


async def members(client):
    admin = await login(client)
    for username in ("alice", "bob"):
        response = await client.post(
            "/auth/users", headers=admin, json={"username": username, "password": "pass123", "role": "user"}
        )
        assert response.status_code == 200, response.text
    return admin, await login(client, "alice", "pass123"), await login(client, "bob", "pass123")


async def create(client, headers, kind, title, **extra):
    plural = {"course": "courses", "article": "articles", "video": "videos", "path": "paths"}[kind]
    payload = (
        {"name": title, "items": []}
        if kind == "path"
        else {"title": title, "url": f"https://example.com/{kind}/{title}", "description": "Useful learning"}
    )
    response = await client.post(f"/{plural}", headers=headers, json=payload | extra)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.anyio
async def test_cookie_transport_csrf_header_precedence_and_logout(app_client):
    await login(app_client)
    denied = await app_client.post("/auth/browser/login", json={"username": "admin", "password": "admin"})
    assert denied.status_code == 403
    response = await app_client.post(
        "/auth/browser/login", headers={"Origin": "http://localhost:8080"}, json={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200, response.text
    assert "token" not in response.json()
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]
    csrf = response.json()["csrf_token"]
    assert (await app_client.get("/auth/browser/session")).status_code == 200
    assert (await app_client.get("/catalog", headers={"X-Session-Token": "invalid"})).status_code == 401
    assert (await app_client.get("/catalog", headers={"X-Session-Token": ""})).status_code == 401
    assert (await app_client.post("/courses", json={"title": "Bad", "description": "Bad"})).status_code == 403
    headers = {"Origin": "http://localhost:8080", "X-CSRF-Token": csrf}
    assert (await app_client.post("/courses", headers=headers | {"Origin": "https://evil.example"}, json={})).status_code == 403
    await create(app_client, headers, "course", "Browser")
    assert (await app_client.post("/auth/browser/logout", headers=headers)).status_code == 200
    assert (await app_client.get("/auth/browser/session")).status_code == 401


@pytest.mark.anyio
async def test_logout_only_current_session_and_reset_revokes_all(app_client):
    admin, alice, _ = await members(app_client)
    alice_second = await login(app_client, "alice", "pass123")
    assert (await app_client.post("/auth/logout", headers=alice)).status_code == 200
    assert (await app_client.get("/auth/me", headers=alice)).status_code == 401
    assert (await app_client.get("/auth/me", headers=alice_second)).status_code == 200
    response = await app_client.post("/auth/users/reset", headers=admin, json={"username": "alice", "password": "newpass"})
    assert response.status_code == 200
    assert (await app_client.get("/auth/me", headers=alice_second)).status_code == 401
    refreshed = await login(app_client, "alice", "newpass")
    await app_client.post("/auth/users/disable", headers=admin, json={"username": "alice", "disabled": True})
    assert (await app_client.get("/catalog", headers=refreshed)).status_code == 401


@pytest.mark.anyio
@pytest.mark.parametrize("kind", ["course", "article", "video", "path"])
async def test_note_contract_and_content_ownership(app_client, kind):
    admin, alice, bob = await members(app_client)
    item = await create(app_client, alice, kind, "Note", recommendation_note="  Helpful context  ")
    assert item["recommendation_note"] == "Helpful context"
    base = f"/{ {'course': 'courses', 'article': 'articles', 'video': 'videos', 'path': 'paths'}[kind] }/{item['id']}"
    change = {"name": "New name", "items": []} if kind == "path" else {"title": "New title"}
    assert (await app_client.put(base, headers=bob, json=change)).status_code == 403
    response = await app_client.put(base, headers=alice, json=change)
    assert response.status_code == 200, response.text
    assert response.json()["recommendation_note"] == "Helpful context"
    response = await app_client.put(base, headers=admin, json=change | {"recommendation_note": None})
    assert response.status_code == 200, response.text
    assert response.json()["recommendation_note"] is None
    assert (await app_client.put(base, headers=alice, json=change | {"recommendation_note": "x" * 1001})).status_code == 422
    assert (await app_client.delete(base, headers=bob)).status_code == 403
    assert (await app_client.delete(base, headers=alice)).status_code == 200
    assert (await app_client.get(base, headers=alice)).status_code == 404


@pytest.mark.anyio
async def test_catalog_is_globally_paginated_and_filterable(app_client):
    admin = await login(app_client)
    for kind, title in [("article", "Bravo"), ("video", "Alpha"), ("path", "Charlie"), ("course", "Delta")]:
        await create(app_client, admin, kind, title)
    first = await app_client.get("/catalog?sort=title&page_size=2", headers=admin)
    assert first.status_code == 200, first.text
    assert [r["title"] for r in first.json()["items"]] == ["Alpha", "Bravo"]
    assert first.json()["total"] == 4
    second = await app_client.get("/catalog?sort=title&page_size=2&page=2", headers=admin)
    assert [r["title"] for r in second.json()["items"]] == ["Charlie", "Delta"]
    assert (await app_client.get("/catalog?type=course&q=Delta&author=admin", headers=admin)).json()["total"] == 1
    assert (await app_client.get("/catalog?page_size=101", headers=admin)).status_code == 422
    assert (await app_client.get("/articles/reviews/summary", headers=admin)).status_code == 200


@pytest.mark.anyio
async def test_activity_covers_all_types_without_private_tracking(app_client):
    _, alice, bob = await members(app_client)
    for kind in ("course", "article", "video", "path"):
        item = await create(app_client, alice, kind, f"Activity {kind}")
        plural = {"course": "courses", "article": "articles", "video": "videos", "path": "paths"}[kind]
        response = await app_client.post(f"/{plural}/{item['id']}/reviews", headers=bob, json={"rating": 4, "text": "Helpful"})
        assert response.status_code == 200, response.text
        if kind == "course":
            await app_client.post("/tracking", headers=bob, json={"course_id": item["id"], "status": "completed"})
    response = await app_client.get("/activity?scope=shared", headers=alice)
    assert response.status_code == 200, response.text
    events = response.json()["items"]
    assert len(events) == 8
    assert {e["type"] for e in events if e["event_type"] == "share"} == {"course", "article", "video", "path"}
    assert all(e["event_type"] in {"share", "review"} for e in events)
    assert (await app_client.get("/activity?scope=personal", headers=alice)).json()["total"] == 4
    assert (await app_client.get("/activity?scope=personal", headers=bob)).json()["total"] == 0
    assert (await app_client.get("/learning/summary", headers=alice)).json()["completed"] == 0
    assert (await app_client.get("/learning/summary", headers=bob)).json()["completed"] == 1
    assert (await app_client.get("/tracking/stats/users", headers=alice)).status_code == 403


@pytest.mark.anyio
async def test_next_course_path_progress_and_reference_deletion(app_client):
    _, alice, _ = await members(app_client)
    first = await create(app_client, alice, "course", "First")
    second = await create(app_client, alice, "course", "Second")
    article = await create(app_client, alice, "article", "Read")
    path = await create(
        app_client,
        alice,
        "path",
        "Sequence",
        items=[
            {"type": "article", "id": article["id"]},
            {"type": "course", "id": first["id"]},
            {"type": "course", "id": second["id"]},
        ],
    )
    await app_client.post(f"/paths/{path['id']}/select", headers=alice)
    response = await app_client.get("/learning/summary", headers=alice)
    assert response.status_code == 200, response.text
    assert response.json()["next_course"]["id"] == first["id"]
    await app_client.post("/tracking", headers=alice, json={"course_id": second["id"], "status": "in_progress"})
    assert (await app_client.get("/learning/summary", headers=alice)).json()["next_course"]["id"] == second["id"]
    await app_client.post("/tracking", headers=alice, json={"course_id": first["id"], "status": "completed"})
    progress = (await app_client.get(f"/learning/paths/{path['id']}", headers=alice)).json()
    assert progress["completed"] == 1 and progress["total"] == 2
    await app_client.delete(f"/articles/{article['id']}", headers=alice)
    remaining = (await app_client.get(f"/paths/{path['id']}", headers=alice)).json()["items"]
    assert [r["id"] for r in remaining] == [first["id"], second["id"]]
    for item in (first, second):
        await app_client.delete(f"/courses/{item['id']}", headers=alice)
    assert (await app_client.get(f"/paths/{path['id']}", headers=alice)).json()["items"] == []
    assert (await app_client.get(f"/learning/paths/{path['id']}", headers=alice)).json()["total"] == 0


@pytest.mark.anyio
async def test_retired_routes_are_not_exposed(app_client):
    admin = await login(app_client)
    assert (await app_client.get("/teams/mine", headers=admin)).status_code == 404
    assert (await app_client.post("/ai/plan", headers=admin, json={"goal": "Python"})).status_code == 404


@pytest.mark.anyio
async def test_production_cookies_and_origin(app_client, monkeypatch):
    await login(app_client)
    production = Settings(
        environment="production",
        public_origin="https://learning.example",
        browser_secret="a" * 48,
        bootstrap_admin_password="test-bootstrap-credential",
    )
    monkeypatch.setattr(browser_auth, "settings", production)
    monkeypatch.setattr(browser_security, "settings", production)
    payload = {"username": "admin", "password": "admin"}
    denied = await app_client.post("/auth/browser/login", headers={"Origin": "http://localhost:8080"}, json=payload)
    assert denied.status_code == 403
    response = await app_client.post("/auth/browser/login", headers={"Origin": production.public_origin}, json=payload)
    assert response.status_code == 200
    assert "Secure" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    with pytest.raises(ValueError, match="BROWSER_SECRET"):
        Settings(environment="production", browser_secret="short")


@pytest.mark.anyio
async def test_read_query_counts_do_not_grow_with_catalog(app_client):
    admin = await login(app_client)
    endpoints = ("/catalog", "/learning/summary", "/learning/items?view=contributions", "/activity?scope=shared")
    statements = []

    def count_query(_conn, _cursor, statement, _parameters, _context, _many):
        statements.append(statement)

    async def measure():
        counts = []
        for endpoint in endpoints:
            statements.clear()
            response = await app_client.get(endpoint, headers=admin)
            assert response.status_code == 200, response.text
            counts.append(len(statements))
        return counts

    event.listen(Engine, "before_cursor_execute", count_query)
    try:
        before = await measure()
        for number in range(8):
            await create(app_client, admin, "course", f"Bounded-{number}")
        after = await measure()
        assert before == after
        assert max(after) <= 10
        response = await app_client.get("/catalog?page_size=3", headers=admin)
        assert len(response.json()["items"]) == 3
        assert response.json()["total"] == 8
    finally:
        event.remove(Engine, "before_cursor_execute", count_query)


@pytest.mark.anyio
async def test_facets_are_filtered_searchable_bounded_and_authenticated(app_client):
    admin, alice, _ = await members(app_client)
    await create(app_client, alice, "course", "Reference One", provider="Alpha", category="Backend")
    await create(app_client, alice, "course", "Reference Two", provider="Beta", category="Backend")
    await create(app_client, admin, "course", "Other", provider="Gamma", category="Web")
    assert (await app_client.get("/catalog/facets?field=provider")).status_code == 401
    response = await app_client.get(
        "/catalog/facets?field=provider&provider=Alpha&category=Backend&q=Reference&page_size=1", headers=alice
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"items": ["Alpha"], "total": 2, "page": 1, "page_size": 1}
    response = await app_client.get("/catalog/facets?field=provider&option_q=bet&author=alice", headers=alice)
    assert response.json()["items"] == ["Beta"]
    response = await app_client.get("/catalog/facets?field=category&category=Web&provider=Alpha", headers=alice)
    assert response.json()["items"] == ["Backend"]
    assert (await app_client.get("/catalog/facets?field=created_by", headers=alice)).status_code == 422
    assert (await app_client.get("/catalog/facets?field=provider&page_size=101", headers=alice)).status_code == 422


@pytest.mark.anyio
async def test_selected_path_totals_are_personal_and_absent_from_catalog(app_client):
    _, alice, bob = await members(app_client)
    course = await create(app_client, alice, "course", "Learning")
    article = await create(app_client, alice, "article", "Reading")
    path = await create(
        app_client,
        alice,
        "path",
        "Mixed",
        items=[{"type": "course", "id": course["id"]}, {"type": "article", "id": article["id"]}],
    )
    empty = await create(app_client, alice, "path", "Empty")
    for headers in (alice, bob):
        for item in (path, empty):
            await app_client.post(f"/paths/{item['id']}/select", headers=headers)
    await app_client.post("/tracking", headers=alice, json={"course_id": course["id"], "status": "completed"})
    for headers, completed in ((alice, 1), (bob, 0)):
        response = await app_client.get("/learning/items?view=paths", headers=headers)
        assert response.status_code == 200, response.text
        items = {item["id"]: item for item in response.json()["items"]}
        assert items[path["id"]]["course_progress"] == {"completed": completed, "total": 1}
        assert items[empty["id"]]["course_progress"] == {"completed": 0, "total": 0}
    catalog = (await app_client.get("/catalog", headers=alice)).json()["items"]
    assert all("course_progress" not in item for item in catalog)


@pytest.mark.anyio
async def test_article_summary_survives_edits_and_reaches_catalog_and_paths(app_client):
    admin, alice, bob = await members(app_client)
    article = await create(app_client, alice, "article", "Summary", description="  Searchable learning value  ")
    base = f"/articles/{article['id']}"
    assert article["description"] == "Searchable learning value"
    assert (await app_client.put(base, headers=bob, json={"description": "No"})).status_code == 403
    renamed = await app_client.put(base, headers=alice, json={"title": "Renamed"})
    assert renamed.json()["description"] == "Searchable learning value"
    catalog = await app_client.get("/catalog?q=Searchable", headers=alice)
    assert catalog.json()["total"] == 1
    assert catalog.json()["items"][0]["description"] == "Searchable learning value"
    mine = await app_client.get("/learning/items?view=contributions", headers=alice)
    assert mine.json()["items"][0]["description"] == "Searchable learning value"
    path = await create(
        app_client, alice, "path", "Summary path", items=[{"type": "article", "id": article["id"], "position": 0}]
    )
    details = await app_client.get(f"/paths/{path['id']}", headers=alice)
    assert details.json()["items"][0]["description"] == "Searchable learning value"
    assert (await app_client.put(base, headers=alice, json={"description": "x" * 2001})).status_code == 422
    assert (
        await app_client.post(
            "/articles", headers=alice, json={"title": "Too long", "url": "https://example.com/long", "description": "x" * 2001}
        )
    ).status_code == 422
    for value in ("   ", None):
        assert (await app_client.put(base, headers=admin, json={"description": value})).json()["description"] is None
    assert (await app_client.put(base, headers=alice, json={"description": "x" * 2000})).status_code == 200


@pytest.mark.anyio
async def test_continue_metadata_uses_current_users_status(app_client):
    _, alice, bob = await members(app_client)
    course = await create(app_client, alice, "course", "Continue metadata", provider="Learning Lab", duration_hours=4)
    await app_client.post("/tracking", headers=alice, json={"course_id": course["id"], "status": "in_progress"})
    await app_client.post("/tracking", headers=bob, json={"course_id": course["id"], "status": "completed"})
    next_course = (await app_client.get("/learning/summary", headers=alice)).json()["next_course"]
    assert next_course["id"] == course["id"]
    assert next_course["url"] == course["url"]
    assert next_course["provider"] == "Learning Lab"
    assert next_course["duration_hours"] == 4
    assert next_course["status"] == "in_progress"
    assert (await app_client.get("/learning/summary", headers=bob)).json()["next_course"] is None


@pytest.mark.anyio
@pytest.mark.parametrize("kind", ["course", "article", "video", "path"])
async def test_activity_excerpts_precedence_bounds_and_current_records(app_client, kind):
    """Shares and reviews expose bounded current text without personal progress."""
    _, alice, bob = await members(app_client)
    plural = {"course": "courses", "article": "articles", "video": "videos", "path": "paths"}[kind]
    item = await create(
        app_client, alice, kind, "Excerpt", description="  Description fallback  ", recommendation_note="  Recommended first  "
    )
    base = f"/{plural}/{item['id']}"
    required = {"name": "Excerpt", "items": [], "description": "Description fallback"} if kind == "path" else {}
    review = await app_client.post(base + "/reviews", headers=bob, json={"rating": 4, "text": "  " + "x" * 300 + "  "})
    assert review.status_code == 200
    events = (await app_client.get("/activity?scope=shared", headers=alice)).json()["items"]
    shared = next(e for e in events if e["event_type"] == "share")
    reviewed = next(e for e in events if e["event_type"] == "review")
    assert (shared["excerpt"], shared["excerpt_kind"]) == ("Recommended first", "recommendation")
    assert reviewed["excerpt"] == "x" * 279 + "…"
    assert reviewed["excerpt_kind"] == "review"
    assert not any(key in reviewed for key in ("status", "course_progress", "tracking"))
    assert (await app_client.put(base, headers=alice, json=required | {"recommendation_note": None})).status_code == 200
    events = (await app_client.get("/activity?scope=shared", headers=alice)).json()["items"]
    shared = next(e for e in events if e["event_type"] == "share")
    assert (shared["excerpt"], shared["excerpt_kind"]) == ("Description fallback", "description")
    if kind != "course":
        assert (await app_client.put(base, headers=alice, json=required | {"description": " "})).status_code == 200
    assert (await app_client.post(base + "/reviews", headers=bob, json={"rating": 3, "text": " \n\t "})).status_code == 200
    events = (await app_client.get("/activity?scope=shared", headers=alice)).json()["items"]
    assert all(
        e["excerpt"] is None and e["excerpt_kind"] is None for e in events if kind != "course" or e["event_type"] == "review"
    )
    personal = (await app_client.get("/activity?scope=personal", headers=alice)).json()
    assert personal["total"] == 1 and personal["items"][0]["actor"] == "bob"
    first = (await app_client.get("/activity?scope=shared&page_size=1", headers=alice)).json()
    second = (await app_client.get("/activity?scope=shared&page_size=1&page=2", headers=alice)).json()
    assert first["total"] == second["total"] == 2
    assert first["items"][0]["event_id"] != second["items"][0]["event_id"]
