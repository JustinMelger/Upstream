import { expect, type Page, test } from "@playwright/test";

const course = {
  id: 71,
  type: "course",
  title: "Designing reliable systems",
  description: "A practical introduction to resilient services.",
  url: "https://example.com/course",
  created_by: "maya",
  provider: "Systems Academy",
  duration_hours: 6,
  level: "Intermediate",
  recommendation_note: "Start with the examples.",
  review_count: 0,
  rating: 0,
};
const pageOf = (items: unknown[], page_size = 24) => ({
  items,
  total: items.length,
  page: 1,
  page_size,
});

async function session(page: Page, role = "user") {
  await page.route("**/api/auth/browser/session", (route) =>
    route.fulfill({
      json: {
        username: "alex",
        role,
        expires_at: "2030-01-01",
        csrf_token: "test",
      },
    }),
  );
}

test("mobile details preserve status on failure and distinguish unavailable reviews", async ({
  page,
}) => {
  await session(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/api/courses/71", (route) =>
    route.fulfill({ json: course }),
  );
  await page.route("**/api/learning/items?**", (route) =>
    route.fulfill({ json: pageOf([{ ...course, status: "in_progress" }]) }),
  );
  await page.route("**/api/courses/71/reviews", (route) =>
    route.fulfill({
      status: 503,
      json: { detail: "Reviews temporarily unavailable" },
    }),
  );
  await page.route("**/api/tracking", (route) =>
    route.fulfill({
      status: 503,
      json: { detail: "Try your progress update again" },
    }),
  );
  await page.goto("/explore/courses/71");
  const action = page.getByRole("link", { name: "Continue learning" });
  await expect(action).toBeVisible();
  const box = await action.boundingBox();
  expect(box!.y + box!.height).toBeLessThan(844);
  await expect(page.getByText(course.description, { exact: true })).toHaveCount(
    1,
  );
  await expect(
    page.getByText("Rating unavailable", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("No reviews yet", { exact: true })).toHaveCount(
    0,
  );
  await expect(
    page.getByRole("link", { name: "Edit", exact: true }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Mark completed", exact: true })
    .click();
  await expect(
    page
      .getByRole("alert")
      .filter({ hasText: "Try your progress update again" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Designing reliable systems: course progress",
    }),
  ).toContainText("in progress");
  await page.route("**/api/courses/71/reviews", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(page.getByText("No reviews yet")).toBeVisible();
  await page.getByRole("button", { name: "Write a review" }).click();
  await expect(page.getByLabel("Your experience")).toBeFocused();
});

test("mixed path mobile statuses stay explicit without per-item requests", async ({
  page,
}) => {
  await session(page);
  await page.setViewportSize({ width: 390, height: 844 });
  const requests: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname.startsWith("/api/"))
      requests.push(new URL(request.url()).pathname);
  });
  await page.route("**/api/paths/72", (route) =>
    route.fulfill({
      json: {
        id: 72,
        name: "A practical learning path",
        created_by: "maya",
        items: [
          { ...course },
          { id: 73, title: "Thoughtful reviews", type: "article" },
          { id: 74, title: "Clear explanations", type: "video" },
        ],
      },
    }),
  );
  await page.route("**/api/paths/72/reviews", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/learning/paths/72", (route) =>
    route.fulfill({
      json: {
        selected: true,
        status: "completed",
        completed: 0,
        total: 1,
        courses: [{ id: 71, status: "in_progress" }],
      },
    }),
  );
  await page.goto("/explore/paths/72");
  await expect(page.locator("ol li")).toHaveCount(3);
  await expect(page.locator("ol li").first()).toContainText("in progress");
  await expect(page.getByLabel("Path status")).toHaveValue("completed");
  await expect(page.getByText("0 of 1 courses completed")).toBeVisible();
  expect(new Set(requests)).toEqual(
    new Set([
      "/api/auth/browser/session",
      "/api/paths/72",
      "/api/paths/72/reviews",
      "/api/learning/paths/72",
    ]),
  );
  await page.route("**/api/learning/paths/72", (route) =>
    route.fulfill({
      json: {
        selected: true,
        status: "completed",
        completed: 0,
        total: 0,
        courses: [],
      },
    }),
  );
  await page.route("**/api/paths/72", (route) =>
    route.fulfill({ json: { id: 72, name: "An empty path", items: [] } }),
  );
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "This path is empty." }),
  ).toBeVisible();
  await expect(page.getByRole("progressbar")).toHaveCount(0);
});

test("profile uses bounded contributions and activity excerpts link to reviews", async ({
  page,
}) => {
  await session(page);
  const collections: string[] = [];
  await page.route("**/api/learning/summary", (route) =>
    route.fulfill({
      json: {
        in_progress: 3,
        completed: 2,
        selected_paths: 1,
        contributions: 1,
        interested: 0,
        next_course: null,
      },
    }),
  );
  await page.route("**/api/learning/items?**", (route) => {
    collections.push(new URL(route.request().url()).search);

    return route.fulfill({
      json: pageOf([{ ...course, created_by: "alex" }], 3),
    });
  });
  await page.goto("/profile");
  await expect(
    page.getByRole("heading", { name: "alex", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Designing reliable systems", exact: true }),
  ).toBeVisible();
  expect(new Set(collections)).toEqual(
    new Set(["?view=contributions&page=1&page_size=3"]),
  );
  await expect(
    page.getByRole("link", { name: "3 In progress" }),
  ).toHaveAttribute("href", "/home?view=tracked&status=in_progress");
  await page.route("**/api/activity?**", (route) =>
    route.fulfill({
      json: pageOf([
        {
          event_id: "review:course:7",
          event_type: "review",
          type: "course",
          content_id: 71,
          title: course.title,
          actor: "sam",
          happened_at: "2026-09-09T10:30:00Z",
          rating: 4,
          excerpt: "Useful practical examples",
          excerpt_kind: "review",
        },
      ]),
    }),
  );
  await page.goto("/activity");
  await expect(page.getByRole("button", { name: "For you" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.getByText("“Useful practical examples”")).toBeVisible();
  await expect(
    page.getByRole("link", {
      name: "Read review of Designing reliable systems",
    }),
  ).toHaveAttribute("href", "/explore/courses/71?view=reviews#reviews");
  await page
    .getByRole("button", { name: "Shared activity", exact: true })
    .click();
  await expect(page).toHaveURL(/scope=shared/);
  await page.goBack();
  await expect(page.getByRole("button", { name: "For you" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
});

test("admin mobile dialogs preserve failed input and restore keyboard focus", async ({
  page,
}) => {
  await session(page, "admin");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/api/auth/users", (route) =>
    route.request().method() === "GET"
      ? route.fulfill({
          json: [
            { username: "alex", role: "admin", disabled: false },
            { username: "sam", role: "user", disabled: false },
          ],
        })
      : route.fulfill({
          status: 409,
          json: { detail: "username already exists" },
        }),
  );
  await page.route("**/api/auth/users/reset", (route) =>
    route.fulfill({ status: 503, json: { detail: "Try again shortly" } }),
  );
  await page.goto("/admin/users");
  await page.getByRole("button", { name: "Add member", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Username", { exact: true }).fill("sam");
  await dialog.getByLabel("Initial password").fill("sample-password-123");
  await dialog.getByRole("button", { name: "Create account" }).click();
  await expect(dialog.getByRole("alert")).toContainText(
    "username already exists",
  );
  await expect(dialog.getByLabel("Username", { exact: true })).toHaveValue(
    "sam",
  );
  await dialog.getByRole("button", { name: "Cancel" }).click();
  await expect(
    page.getByRole("button", { name: "Add member", exact: true }),
  ).toBeFocused();
  await page.getByRole("button", { name: "Manage alex" }).click();
  await expect(
    page.getByRole("menuitem", { name: "Disable account" }),
  ).toHaveAttribute("aria-disabled", "true");
  await expect(
    page.getByRole("menuitem", { name: "Delete account" }),
  ).toHaveAttribute("aria-disabled", "true");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Manage sam" }).click();
  await page.getByRole("menuitem", { name: "Reset password" }).click();
  await dialog.getByLabel("New password").fill("new-password-123");
  await dialog
    .getByRole("button", { name: "Reset password", exact: true })
    .click();
  await expect(dialog.getByRole("alert")).toContainText("Try again shortly");
  await expect(dialog.getByLabel("New password")).toHaveValue(
    "new-password-123",
  );
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Manage sam" })).toBeFocused();
});

for (const mode of ["create", "reset"] as const) {
  test(`admin ${mode} explains password length and prevents invalid requests`, async ({
    page,
  }) => {
    await session(page, "admin");
    let submissions = 0;
    await page.route("**/api/auth/users", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          json: [{ username: "sam", role: "user", disabled: false }],
        });
      } else {
        submissions += 1;
        await route.fulfill({ json: { username: "sam", role: "user" } });
      }
    });
    await page.route("**/api/auth/users/reset", async (route) => {
      submissions += 1;
      await route.fulfill({ json: { updated: 1 } });
    });
    await page.goto("/admin/users");

    if (mode === "create") {
      await page
        .getByRole("button", { name: "Add member", exact: true })
        .click();
      await page.getByLabel("Username", { exact: true }).fill("sam");
    } else {
      await page.getByRole("button", { name: "Manage sam" }).click();
      await page.getByRole("menuitem", { name: "Reset password" }).click();
    }

    const dialog = page.getByRole("dialog");
    const password = dialog.getByLabel(
      mode === "create" ? "Initial password" : "New password",
      { exact: true },
    );
    const submit = dialog.getByRole("button", {
      name: mode === "create" ? "Create account" : "Reset password",
      exact: true,
    });
    await expect(dialog.getByText("Use at least 12 characters.")).toBeVisible();
    await password.fill("short-pass1");
    await submit.click();
    await expect(dialog.getByRole("alert")).toHaveText(
      "Password must contain at least 12 characters.",
    );
    await expect(password).toBeFocused();
    await expect(password).toHaveValue("short-pass1");
    await expect(password).toHaveAttribute("aria-invalid", "true");
    expect(submissions).toBe(0);
    await password.fill("            ");
    await submit.click();
    await expect(dialog.getByRole("alert")).toHaveText("Enter a password.");
    expect(submissions).toBe(0);
    await password.fill("exactly-12!!");
    await submit.click();
    await expect(dialog).not.toBeVisible();
    expect(submissions).toBe(1);
  });
}

test("admin role changes confirm, recover, refresh and restore focus", async ({
  page,
}) => {
  await session(page, "admin");
  let role = "user";
  let attempts = 0;
  let release: (() => void) | undefined;
  await page.route("**/api/auth/users", (route) =>
    route.fulfill({
      json: [
        { username: "alex", role: "admin", disabled: false },
        { username: "sam", role, disabled: false },
      ],
    }),
  );
  await page.route("**/api/auth/users/sam/role", async (route) => {
    expect(route.request().method()).toBe("PATCH");
    expect(route.request().headers()["x-csrf-token"]).toBeTruthy();
    attempts += 1;

    if (attempts === 1) {
      await new Promise<void>((resolve) => {
        release = resolve;
      });
      await route.fulfill({
        status: 409,
        json: { message: "last_admin_required" },
      });

      return;
    }

    role = route.request().postDataJSON().role;
    await route.fulfill({ json: { username: "sam", role } });
  });
  await page.goto("/admin/users");
  await page.getByRole("button", { name: "Manage alex" }).click();
  await expect(
    page.getByRole("menuitem", { name: "Make member" }),
  ).toHaveAttribute("aria-disabled", "true");
  await page.keyboard.press("Escape");
  const manage = page.getByRole("button", { name: "Manage sam" });
  await manage.click();
  await page.getByRole("menuitem", { name: "Make admin" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("Make sam an admin?");
  await dialog.getByRole("button", { name: "Cancel" }).click();
  await expect(manage).toBeFocused();
  expect(attempts).toBe(0);
  await manage.click();
  await page.getByRole("menuitem", { name: "Make admin" }).click();
  await dialog.getByRole("button", { name: "Make admin", exact: true }).click();
  await expect(dialog.getByRole("button", { name: "Saving…" })).toBeDisabled();
  await expect(dialog.getByRole("button", { name: "Cancel" })).toBeDisabled();
  await expect.poll(() => !!release).toBe(true);
  release!();
  await expect(dialog.getByRole("alert")).toContainText(
    "Keep at least one enabled administrator",
  );
  await dialog.getByRole("button", { name: "Make admin", exact: true }).click();
  await expect(dialog).not.toBeVisible();
  await expect(manage).toBeFocused();
  await manage.click();
  await page.getByRole("menuitem", { name: "Make member" }).click();
  await expect(dialog).toContainText("Make sam a member?");
  await expect(dialog.getByRole("alert")).toHaveCount(0);
  await dialog
    .getByRole("button", { name: "Make member", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await manage.click();
  await expect(
    page.getByRole("menuitem", { name: "Make admin" }),
  ).toBeVisible();
  expect(attempts).toBe(3);
});

test("profile identity and contributions survive a summary failure", async ({
  page,
}) => {
  await session(page);
  await page.route("**/api/learning/summary", (route) =>
    route.fulfill({ status: 503, json: { detail: "Totals are unavailable" } }),
  );
  await page.route("**/api/learning/items?**", (route) =>
    route.fulfill({ json: pageOf([], 3) }),
  );
  await page.goto("/profile");
  await expect(
    page.getByRole("heading", { name: "alex", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("Totals are unavailable");
  await expect(
    page.getByRole("heading", {
      name: "Your library starts with one good find.",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Share something" }),
  ).toBeVisible();
  await page.goto("/admin/users");
  await expect(
    page.getByRole("heading", { name: "Administrator access required." }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Add member", exact: true }),
  ).toHaveCount(0);
});

test("long article details and failed artwork retain readable content and mobile actions", async ({
  page,
}) => {
  await session(page);
  await page.setViewportSize({ width: 390, height: 844 });
  const description = "A practical guide to giving useful feedback. ".repeat(
    12,
  );
  await page.route("**/api/articles/73", (route) =>
    route.fulfill({
      json: {
        id: 73,
        title: "Thoughtful code reviews for distributed engineering teams",
        description,
        created_by: "maya",
        url: "https://example.com/article",
      },
    }),
  );
  await page.route("**/api/articles/73/reviews", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/artwork/**", (route) => route.abort());
  await page.goto("/explore/articles/73");
  const action = page.getByRole("link", { name: "Read article", exact: true });
  await expect(action).toBeVisible();
  const box = await action.boundingBox();
  expect(box!.y + box!.height).toBeLessThan(844);
  await expect(
    page.getByRole("heading", { name: "About this article" }),
  ).toBeVisible();
  await expect(
    page.getByText(description.trim(), { exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel("Your progress")).toHaveCount(0);
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.goto("/explore/articles/73?view=reviews#reviews");
  await expect(page.locator("#reviews")).toBeInViewport();
});
