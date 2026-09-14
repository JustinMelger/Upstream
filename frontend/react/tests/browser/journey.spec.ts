import { expect, type Page, test } from "@playwright/test";

const course = {
  id: 80,
  type: "course",
  title: "Journey course",
  url: "https://course.example.test/learn",
  description: "Learn through practical examples.",
  created_by: "maya",
  rating: 0,
  review_count: 0,
};

async function fixture(
  page: Page,
  initial: string | null = null,
  pathSuggestion = false,
  url: string | null = course.url,
) {
  const state = {
    status: initial,
    fail: false,
    writes: [] as (string | null)[],
  };
  const pageOf = (items: unknown[]) => ({
    items,
    total: items.length,
    page: 1,
    page_size: 24,
  });
  await page.context().route("https://course.example.test/**", (route) =>
    route.fulfill({
      contentType: "text/html",
      body: "<h1>External course</h1>",
    }),
  );
  await page.route("**/api/**", async (route) => {
    if (!new URL(route.request().url()).pathname.startsWith("/api/"))
      return route.fallback();
    const parsed = new URL(route.request().url());
    const path = parsed.pathname.slice(4);
    let body: unknown;
    if (path === "/auth/browser/session")
      body = {
        username: "alex",
        role: "user",
        expires_at: "2030-01-01",
        csrf_token: "test",
      };
    else if (path === "/courses/80") body = { ...course, url };
    else if (path === "/courses/80/reviews") body = [];
    else if (path === "/tracking" || path === "/tracking/delete") {
      if (state.fail)
        return route.fulfill({
          status: 503,
          json: { detail: "Could not save progress" },
        });
      state.status =
        path === "/tracking/delete"
          ? null
          : route.request().postDataJSON().status;
      state.writes.push(state.status);
      body = { course_id: 80, status: state.status };
    } else if (path === "/learning/summary")
      body = {
        interested: Number(state.status === "interested"),
        in_progress: Number(state.status === "in_progress"),
        completed: Number(state.status === "completed"),
        selected_paths: Number(pathSuggestion),
        contributions: 0,
        next_course:
          state.status === "in_progress" ||
          (pathSuggestion && state.status !== "completed")
            ? { ...course, url, status: state.status }
            : null,
      };
    else if (path === "/learning/items")
      body = pageOf(
        parsed.searchParams.get("view") === "paths"
          ? []
          : state.status &&
              (!parsed.searchParams.get("status") ||
                parsed.searchParams.get("status") === state.status)
            ? [{ ...course, url, status: state.status }]
            : [],
      );
    else if (path === "/learning/paths/81")
      body = {
        selected: true,
        status: "interested",
        total: 1,
        completed: Number(state.status === "completed"),
        courses: [{ id: 80, status: state.status }],
      };
    else if (path === "/paths/81")
      body = { id: 81, name: "Journey path", items: [course] };
    else if (path === "/paths/81/reviews") body = [];
    else if (path === "/catalog") body = pageOf([course]);
    else if (path === "/catalog/facets") body = pageOf([]);
    else throw new Error(`Unexpected journey request ${path}`);
    await route.fulfill({ json: body });
  });

  return state;
}

test("add, start, complete and Undo preserve the collection and feedback", async ({
  page,
}) => {
  const state = await fixture(page);
  await page.goto("/explore/courses/80");
  await page
    .getByRole("button", { name: "Add to My learning", exact: true })
    .click();
  await expect(page.getByRole("status")).toHaveText(
    "Added to My learning · Interested",
  );
  expect(state.status).toBe("interested");
  await page
    .getByRole("link", { name: "View my learning", exact: true })
    .click();
  await expect(page).toHaveURL(/status=interested/);
  const popup = page.waitForEvent("popup");
  await page
    .getByRole("button", { name: "Start learning", exact: true })
    .click();
  const resource = await popup;
  await expect(
    resource.getByRole("heading", { name: "External course" }),
  ).toBeVisible();
  expect(await resource.evaluate(() => window.opener)).toBeNull();
  await resource.close();
  await expect(page.getByRole("status")).toHaveText("Added to In progress.");
  await page
    .getByRole("link", { name: "View my learning", exact: true })
    .click();
  const complete = page.getByRole("button", {
    name: "Mark completed",
    exact: true,
  });
  await complete.focus();
  await complete.press("Enter");
  const notice = page.getByRole("region", { name: "Learning update" });
  await expect(notice).toContainText("Course completed. Nice work!");
  await expect(page).toHaveURL(/status=in_progress/);
  await expect(complete).toHaveCount(0);
  await expect(notice).toBeFocused();
  await expect(
    page.getByRole("heading", {
      name: "You’ve finished your in-progress courses.",
    }),
  ).toBeVisible();
  await expect(
    notice.getByRole("link", { name: "Review course" }),
  ).toHaveAttribute("href", "/explore/courses/80?view=reviews#reviews");
  state.fail = true;
  await notice.getByRole("button", { name: "Undo" }).click();
  await expect(notice.getByRole("alert")).toContainText(
    "Could not save progress",
  );
  expect(state.status).toBe("completed");
  state.fail = false;
  await notice.getByRole("button", { name: "Undo" }).click();
  await expect(complete).toBeVisible();
  expect(state.status).toBe("in_progress");
  await page.getByRole("link", { name: "Explore", exact: true }).click();
  await expect(notice).toContainText("Completion undone");
  await page.reload();
  await expect(notice).toHaveCount(0);
});

test("failed Start closes its tab; blocked Start offers a manual link", async ({
  page,
}) => {
  const state = await fixture(page, "interested");
  state.fail = true;
  await page.goto("/explore/courses/80");
  const popup = page.waitForEvent("popup");
  await page.getByRole("button", { name: "Start learning" }).click();
  const tab = await popup;
  await expect.poll(() => tab.isClosed()).toBe(true);
  await expect(page.getByRole("alert")).toContainText(
    "previous status is unchanged",
  );
  expect(state.status).toBe("interested");
  state.fail = false;
  await page.evaluate(() => {
    window.open = () => null;
  });
  await page.getByRole("button", { name: "Start learning" }).click();
  const notice = page.getByRole("region", { name: "Learning update" });
  await expect(
    notice.getByRole("link", { name: "Open course" }),
  ).toHaveAttribute("href", course.url);
  expect(state.status).toBe("in_progress");
});

test("an untracked path suggestion starts course tracking without changing the path", async ({
  page,
}) => {
  const state = await fixture(page, null, true);
  await page.goto("/home");
  const next = page.getByRole("region", { name: "Continue learning" });
  await expect(next).toContainText("Your next step");
  const popup = page.waitForEvent("popup");
  await next.getByRole("button", { name: "Start learning" }).click();
  const tab = await popup;
  await expect(
    tab.getByRole("heading", { name: "External course" }),
  ).toBeVisible();
  await tab.close();
  await expect(next).toContainText("Pick up where you left off");
  await page.goto("/explore/paths/81");
  await expect(page.getByLabel("Path status")).toHaveValue("interested");
  await expect(page.getByText("0 of 1 courses completed")).toBeVisible();
  expect(state.writes).toEqual(["in_progress"]);
});

for (const status of [null, "completed"])
  test(`opening ${status || "untracked"} course preserves tracking`, async ({
    page,
  }) => {
    const state = await fixture(page, status);
    await page.goto("/explore/courses/80");
    const popup = page.waitForEvent("popup");
    await page.getByRole("link", { name: "Open course" }).click();
    const tab = await popup;
    await expect(
      tab.getByRole("heading", { name: "External course" }),
    ).toBeVisible();
    await tab.close();
    expect(state.writes).toEqual([]);
  });

test("invalid course URLs expose details and independent status controls", async ({
  page,
}) => {
  const state = await fixture(page, "interested", false, "javascript:alert(1)");
  await page.goto("/home?view=tracked&status=interested");
  await expect(
    page.getByRole("link", { name: "View details", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Start learning" }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Journey course: course progress" })
    .click();
  await page
    .getByRole("menuitemradio", { name: "completed", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Learning update" }),
  ).toContainText("Course completed");
  await page.getByRole("button", { name: "Undo" }).click();
  await expect(page.getByRole("status")).toContainText("Completion undone");
  expect(state.status).toBe("interested");
});
