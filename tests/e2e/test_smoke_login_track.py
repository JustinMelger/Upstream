from __future__ import annotations

import os
import re
import time

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


@pytest.mark.integration
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

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                base_url=ui_url,
                viewport={"width": 1440, "height": 1100},
                reduced_motion="reduce",
                color_scheme="dark",
            )
            page = await context.new_page()

            await page.goto("/login", wait_until="networkidle")
            await page.get_by_label("Username").fill("admin")
            await page.get_by_label("Password").fill("admin")
            await page.get_by_role("button", name="Login").click()
            await page.wait_for_url(re.compile(r".*/home(?:\?.*)?$"), timeout=15000)
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
            await page.get_by_label("Rating").select_option("5")
            await page.get_by_label("Comment (optional)").fill("E2E smoke review")
            await page.get_by_role("button", name="Save review").click()
            await page.get_by_text("Rating: 5/5 · admin").first.wait_for(timeout=15000)
            await assert_visual_snapshot(page=page, name="courses_after_review.png", full_page=False)

            # Path select flow.
            await page.goto(f"/explore/paths/{path_id}", wait_until="networkidle")
            await expect(page.get_by_text(path_name).first).to_be_visible(timeout=15000)
            await page.get_by_role("button", name="Track Path").click()
            await expect(page.get_by_role("button", name="Untrack Path")).to_be_visible(timeout=15000)
            await assert_visual_snapshot(page=page, name="paths_after_select.png", full_page=False)

            await context.close()
            await browser.close()
    except PlaywrightError as exc:  # pragma: no cover - environment/browser install dependent
        _skip_or_fail(f"Playwright/browser not available: {exc}")

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
