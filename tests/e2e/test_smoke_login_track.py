from __future__ import annotations

import os
import re
import time
from typing import Any

import httpx
from playwright.async_api import async_playwright, Error as PlaywrightError, expect
import pytest

from tests.e2e.visual_assertions import assert_visual_snapshot


pytestmark = [pytest.mark.anyio, pytest.mark.e2e]


def _api_base_url() -> str:
    return str(os.getenv("E2E_API_URL", "http://127.0.0.1:8000")).rstrip("/")


def _ui_base_url() -> str:
    return str(os.getenv("E2E_UI_URL", "http://127.0.0.1:8080")).rstrip("/")


def _strict_e2e_env() -> bool:
    return os.getenv("E2E_STRICT_ENV", "0") == "1" or os.getenv("GITHUB_ACTIONS", "").lower() == "true"


def _skip_or_fail(reason: str) -> None:
    if _strict_e2e_env():
        pytest.fail(reason)
    pytest.skip(reason)


async def _select_combobox_option(page, *, label: str, option: str) -> None:
    await page.get_by_label(label).click()
    await page.get_by_role("option", name=option, exact=True).click()


async def _new_browser_context(playwright, *, ui_url: str):
    try:
        browser = await playwright.chromium.launch(headless=True)
    except PlaywrightError as exc:  # pragma: no cover - environment/browser install dependent
        _skip_or_fail(f"Playwright/browser not available: {exc}")
    context = await browser.new_context(
        base_url=ui_url,
        viewport={"width": 1440, "height": 1100},
        reduced_motion="reduce",
        color_scheme="dark",
    )
    return browser, context


async def _login_as_admin(page) -> None:
    await page.goto("/login", wait_until="networkidle")
    await page.get_by_label("Username").fill("admin")
    await page.get_by_label("Password").fill("admin")
    await page.get_by_role("button", name="Login").click()
    await page.wait_for_url(re.compile(r".*/home(?:\?.*)?$"), timeout=15000)


async def _post_or_skip(
    client: httpx.AsyncClient,
    path: str,
    *,
    token: str,
    json: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    response = await client.post(path, json=json, headers={"X-Session-Token": token})
    if response.status_code != 200:
        _skip_or_fail(f"E2E backend {label} unavailable: status={response.status_code} body={response.text[:200]}")
    return dict(response.json() or {})


async def _bootstrap_admin_and_seed_content(
    *,
    api_url: str,
    course_title: str,
    path_name: str,
) -> tuple[str, int, int]:
    try:
        async with httpx.AsyncClient(base_url=api_url, timeout=20.0) as client:
            login = await client.post("/auth/login", json={"username": "admin", "password": "admin"})
            if login.status_code != 200:
                _skip_or_fail(f"E2E backend login unavailable at {api_url}: status={login.status_code} body={login.text[:200]}")
            token = str(login.json()["token"])

            create_course = await client.post(
                "/courses",
                json={"title": course_title, "description": "E2E smoke tracking flow"},
                headers={"X-Session-Token": token},
            )
            if create_course.status_code != 200:
                _skip_or_fail(
                    "E2E backend course seeding unavailable: "
                    f"status={create_course.status_code} body={create_course.text[:200]}"
                )
            course_id = int(create_course.json()["id"])

            create_path = await client.post(
                "/paths",
                json={
                    "name": path_name,
                    "description": "E2E smoke path",
                    "items": [{"type": "course", "id": course_id, "position": 0}],
                },
                headers={"X-Session-Token": token},
            )
            if create_path.status_code != 200:
                _skip_or_fail(
                    f"E2E backend path seeding unavailable: status={create_path.status_code} body={create_path.text[:200]}"
                )
            path_id = int(create_path.json()["id"])

            return token, course_id, path_id
    except httpx.HTTPError as exc:  # pragma: no cover - environment dependent
        _skip_or_fail(f"E2E backend not reachable at {api_url}: {exc}")


async def _bootstrap_mixed_learning_content(
    *,
    api_url: str,
    run_id: int,
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(base_url=api_url, timeout=20.0) as client:
            login = await client.post("/auth/login", json={"username": "admin", "password": "admin"})
            if login.status_code != 200:
                _skip_or_fail(f"E2E backend login unavailable at {api_url}: status={login.status_code} body={login.text[:200]}")
            token = str(login.json()["token"])

            course = await _post_or_skip(
                client,
                "/courses",
                token=token,
                label="course seeding",
                json={
                    "title": f"E2E Checklist Course {run_id}",
                    "description": "E2E checklist course detail",
                    "provider": "E2E Academy",
                    "category": "Testing",
                    "level": "Beginner",
                    "duration_hours": 2,
                    "url": "https://example.com/e2e-course",
                },
            )
            video = await _post_or_skip(
                client,
                "/videos",
                token=token,
                label="video seeding",
                json={
                    "title": f"E2E Checklist Video {run_id}",
                    "description": "E2E checklist video detail",
                    "provider": "YouTube",
                    "category": "Testing",
                    "url": "https://example.com/e2e-video",
                },
            )
            article = await _post_or_skip(
                client,
                "/articles",
                token=token,
                label="article seeding",
                json={
                    "title": f"E2E Checklist Article {run_id}",
                    "url": "https://example.com/e2e-article",
                    "tags": "testing,e2e",
                },
            )
            path = await _post_or_skip(
                client,
                "/paths",
                token=token,
                label="mixed path seeding",
                json={
                    "name": f"E2E Checklist Mixed Path {run_id}",
                    "description": "E2E checklist mixed path detail",
                    "items": [
                        {"type": "course", "id": int(course["id"]), "position": 0},
                        {"type": "video", "id": int(video["id"]), "position": 1},
                        {"type": "article", "id": int(article["id"]), "position": 2},
                    ],
                },
            )
            return {"token": token, "course": course, "video": video, "article": article, "path": path}
    except httpx.HTTPError as exc:  # pragma: no cover - environment dependent
        _skip_or_fail(f"E2E backend not reachable at {api_url}: {exc}")


@pytest.mark.e2e
async def test_smoke_login_track_review_and_select_path() -> None:
    api_url = _api_base_url()
    ui_url = _ui_base_url()
    run_id = int(time.time())
    course_title = f"E2E Track Course {run_id}"
    path_name = f"E2E Select Path {run_id}"
    token, course_id, path_id = await _bootstrap_admin_and_seed_content(
        api_url=api_url,
        course_title=course_title,
        path_name=path_name,
    )

    async with async_playwright() as playwright:
        browser, context = await _new_browser_context(playwright, ui_url=ui_url)
        try:
            page = await context.new_page()

            await _login_as_admin(page)
            await assert_visual_snapshot(page=page, name="home_after_login.png", full_page=False)

            # Track course flow.
            await page.goto(f"/explore/courses/{course_id}", wait_until="networkidle")
            await expect(page.get_by_text(course_title).first).to_be_visible(timeout=15000)
            await page.get_by_role("button", name="Track course").click()
            await expect(page.get_by_text("Status: Interested")).to_be_visible(timeout=15000)
            await page.get_by_role("button", name="Start course").click()
            await expect(page.get_by_text("Status: In Progress")).to_be_visible(timeout=15000)
            await assert_visual_snapshot(page=page, name="courses_after_track.png", full_page=False)

            # Course review flow.
            await page.goto(f"/explore/courses/{course_id}?view=reviews", wait_until="networkidle")
            await _select_combobox_option(page, label="Rating", option="5")
            await page.get_by_label("Comment (optional)").fill("E2E smoke review")
            await page.get_by_role("button", name="Save review").click()
            saved_review = page.locator(".lp-review-entry").filter(has_text="E2E smoke review").first
            await expect(saved_review).to_be_visible(timeout=15000)
            await expect(saved_review.get_by_text("5/5", exact=True)).to_be_visible()
            await expect(saved_review.get_by_text("admin", exact=True)).to_be_visible()
            await assert_visual_snapshot(page=page, name="courses_after_review.png", full_page=False)

            # Path select flow.
            await page.goto(f"/explore/paths/{path_id}", wait_until="networkidle")
            await expect(page.get_by_text(path_name).first).to_be_visible(timeout=15000)
            await page.get_by_role("button", name="Track Path").click()
            await expect(page.get_by_role("button", name="Untrack Path")).to_be_visible(timeout=15000)
            await assert_visual_snapshot(page=page, name="paths_after_select.png", full_page=False)
            await _select_combobox_option(page, label="Rating", option="4")
            await page.get_by_label("Comment (optional)").fill("E2E path smoke review")
            await page.get_by_role("button", name="Save review").click()
            saved_path_review = page.locator(".lp-review-entry").filter(has_text="E2E path smoke review").first
            await expect(saved_path_review).to_be_visible(timeout=15000)
            await expect(saved_path_review.get_by_text("4/5", exact=True)).to_be_visible()
        finally:
            await context.close()
            await browser.close()

    async with httpx.AsyncClient(base_url=api_url, timeout=20.0) as client:
        tracking = await client.get("/tracking", headers={"X-Session-Token": token})
        assert tracking.status_code == 200
        tracking_rows = list(tracking.json() or [])
        assert any(
            int(row.get("course_id") or 0) == course_id and str(row.get("status") or "") == "in_progress"
            for row in tracking_rows
        )

        reviews = await client.get(f"/courses/{course_id}/reviews", headers={"X-Session-Token": token})
        assert reviews.status_code == 200
        review_rows = list(reviews.json() or [])
        assert any(
            int(row.get("course_id") or 0) == course_id
            and str(row.get("created_by") or "") == "admin"
            and int(row.get("rating") or 0) == 5
            for row in review_rows
        )

        selected = await client.get("/paths/selected/list", headers={"X-Session-Token": token})
        assert selected.status_code == 200
        selected_rows = list(selected.json() or [])
        assert any(int(row.get("id") or 0) == path_id for row in selected_rows)

        path_reviews = await client.get(f"/paths/{path_id}/reviews", headers={"X-Session-Token": token})
        assert path_reviews.status_code == 200
        path_review_rows = list(path_reviews.json() or [])
        assert any(
            int(row.get("path_id") or 0) == path_id
            and str(row.get("created_by") or "") == "admin"
            and int(row.get("rating") or 0) == 4
            for row in path_review_rows
        )


@pytest.mark.e2e
async def test_smoke_explore_detail_routes_render_seeded_content() -> None:
    api_url = _api_base_url()
    ui_url = _ui_base_url()
    run_id = int(time.time())
    seeded = await _bootstrap_mixed_learning_content(api_url=api_url, run_id=run_id)
    course = dict(seeded["course"])
    video = dict(seeded["video"])
    article = dict(seeded["article"])
    path = dict(seeded["path"])

    async with async_playwright() as playwright:
        browser, context = await _new_browser_context(playwright, ui_url=ui_url)
        try:
            page = await context.new_page()
            await _login_as_admin(page)

            for tab, title in [
                ("courses", str(course["title"])),
                ("videos", str(video["title"])),
                ("articles", str(article["title"])),
                ("paths", str(path["name"])),
            ]:
                await page.goto(f"/explore?tab={tab}", wait_until="networkidle")
                await expect(page.get_by_text(title).first).to_be_visible(timeout=15000)

            for route, title in [
                (f"/explore/courses/{int(course['id'])}", str(course["title"])),
                (f"/explore/videos/{int(video['id'])}", str(video["title"])),
                (f"/explore/articles/{int(article['id'])}", str(article["title"])),
                (f"/explore/paths/{int(path['id'])}", str(path["name"])),
            ]:
                await page.goto(route, wait_until="networkidle")
                await expect(page.get_by_text(title).first).to_be_visible(timeout=15000)

            await expect(page.get_by_text(str(course["title"])).first).to_be_visible()
            await expect(page.get_by_text(str(video["title"])).first).to_be_visible()
            await expect(page.get_by_text(str(article["title"])).first).to_be_visible()
        finally:
            await context.close()
            await browser.close()


@pytest.mark.e2e
async def test_smoke_share_course_publish_flow() -> None:
    api_url = _api_base_url()
    ui_url = _ui_base_url()
    run_id = int(time.time())
    title = f"E2E Shared Course {run_id}"
    token_payload = await _bootstrap_mixed_learning_content(api_url=api_url, run_id=run_id)
    token = str(token_payload["token"])

    async with async_playwright() as playwright:
        browser, context = await _new_browser_context(playwright, ui_url=ui_url)
        try:
            page = await context.new_page()
            await _login_as_admin(page)

            await page.goto("/share/item?type=course", wait_until="networkidle")
            await page.get_by_label("https://...").fill(f"https://example.com/shared-course-{run_id}")
            await page.get_by_label("Course title").fill(title)
            await page.get_by_label("Description").fill("Course published from the e2e smoke checklist.")
            await page.get_by_label("Provider").fill("E2E Academy")
            await page.get_by_label("Category").fill("Testing")
            await page.get_by_role("button", name="Publish Learning Item").click()
            await page.wait_for_url(re.compile(r".*/explore\?tab=courses$"), timeout=15000)
            await expect(page.get_by_text(title).first).to_be_visible(timeout=15000)
        finally:
            await context.close()
            await browser.close()

    async with httpx.AsyncClient(base_url=api_url, timeout=20.0) as client:
        courses = await client.get("/courses", headers={"X-Session-Token": token}, params={"q": title})
        assert courses.status_code == 200
        assert any(str(row.get("title") or "") == title for row in list(courses.json() or []))


@pytest.mark.e2e
async def test_smoke_teams_and_admin_pages_render() -> None:
    api_url = _api_base_url()
    ui_url = _ui_base_url()
    await _bootstrap_mixed_learning_content(api_url=api_url, run_id=int(time.time()))

    async with async_playwright() as playwright:
        browser, context = await _new_browser_context(playwright, ui_url=ui_url)
        try:
            page = await context.new_page()
            await _login_as_admin(page)

            await page.goto("/teams", wait_until="networkidle")
            await expect(page.get_by_role("button", name="Create team").first).to_be_visible(timeout=15000)
            await expect(page.get_by_text("Inbox").first).to_be_visible(timeout=15000)

            await page.goto("/admin/users", wait_until="networkidle")
            await expect(page.get_by_text("Admin users").first).to_be_visible(timeout=15000)
            await expect(page.get_by_text("User directory").first).to_be_visible(timeout=15000)
            await expect(page.get_by_text("User actions").first).to_be_visible(timeout=15000)
            await expect(page.get_by_role("button", name="Refresh").first).to_be_visible()
        finally:
            await context.close()
            await browser.close()
