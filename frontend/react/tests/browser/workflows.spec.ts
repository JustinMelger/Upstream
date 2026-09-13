import { test, expect, type Page } from "@playwright/test";
async function login(
  page: Page,
  username = "alex",
  password = "learn-demo-123",
) {
  await page.goto("/login");
  await page.getByLabel("Username", { exact: true }).fill(username);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "My learning" }),
  ).toBeVisible();
}
test("discovery, progress, activity and reload", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await login(page);
  await page.getByRole("link", { name: "Explore", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Explore" })).toBeVisible();
  await page
    .getByRole("textbox", { name: "Search learning" })
    .fill("Production");
  await expect(page).toHaveURL(/q=Production/);
  await expect(
    page.getByRole("heading", { name: "Production-ready Python" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Production-ready Python", exact: true })
    .click();
  const progress = page.getByRole("button", {
    name: "Production-ready Python: course progress",
  });
  if (
    await page
      .getByRole("button", { name: "Add to My learning", exact: true })
      .isVisible()
  )
    await page
      .getByRole("button", { name: "Add to My learning", exact: true })
      .click();
  await progress.click();
  await page
    .getByRole("menuitemradio", { name: "completed", exact: true })
    .click();
  await expect(progress).toContainText("completed");
  await page.reload();
  await expect(progress).toContainText("completed");
  await page.goBack();
  await expect(
    page.getByRole("textbox", { name: "Search learning" }),
  ).toHaveValue("Production");
  await page.getByRole("link", { name: "Activity", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Activity" })).toBeVisible();
  await page
    .getByRole("button", { name: "Shared activity", exact: true })
    .click();
  await expect(
    page.getByRole("link", {
      name: "Build services with confidence",
      exact: true,
    }),
  ).toBeVisible();
  await page.goto("/teams");
  await expect(
    page.getByRole("status").filter({ hasText: "Teams has been retired" }),
  ).toContainText("Teams has been retired");
  await page.goto("/profile/stats");
  await expect(
    page.getByRole("heading", { name: "Your learning, at a glance" }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
test("share, edit, review, and delete an article", async ({ page }) => {
  await login(page);
  await page.goto("/share/item?type=article");
  await page
    .getByLabel("Resource URL")
    .fill("https://example.com/browser-article");
  await page.getByLabel("Title", { exact: true }).fill("A better way to learn");
  await page
    .getByLabel("Why do you recommend it?", { exact: false })
    .fill("Clear examples and a thoughtful explanation.");
  await page
    .getByRole("button", { name: /^Share (article|course|video)$/ })
    .click();
  await expect(
    page.getByRole("heading", { name: "A better way to learn" }),
  ).toBeVisible();
  await expect(
    page.getByText("Clear examples and a thoughtful explanation.", {
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByLabel("Your experience")
    .fill("Useful from the first section.");
  await page.getByRole("button", { name: "Share review", exact: true }).click();
  await expect(page.getByText("Your change has been saved.")).toBeVisible();
  await page.getByRole("link", { name: "Edit", exact: true }).click();
  await page
    .getByLabel("Title", { exact: true })
    .fill("A better way to keep learning");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(
    page.getByRole("heading", { name: "A better way to keep learning" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete", exact: true })
    .click();
  await expect(page.getByRole("heading", { name: "Explore" })).toBeVisible();
});
test("mixed path ordering and manual status remain independent", async ({
  page,
}) => {
  await login(page);
  await page.goto("/share/path");
  await page.getByLabel("Path name").fill("My browser learning path");
  await page
    .getByLabel("What will people learn?", { exact: true })
    .fill("A small sequence for a practical learning session.");
  await page.getByRole("button", { name: "Add", exact: true }).first().click();
  await page.getByLabel("Item type").selectOption("video");
  await page.getByRole("button", { name: "Add", exact: true }).first().click();
  await expect(page.locator("ol li")).toHaveCount(2);
  await page
    .getByRole("button", { name: /Move .* up/ })
    .last()
    .press("Enter");
  await expect(page.locator("ol li").first()).toContainText("video");
  await page.getByRole("button", { name: "Share path", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "My browser learning path" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Add to My learning" }).click();
  await page.getByLabel("Path status").selectOption("completed");
  await expect(page.getByLabel("Path status")).toHaveValue("completed");
  await expect(page.getByText(/of 1 courses completed/)).toBeVisible();
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete", exact: true })
    .click();
  await expect(page.getByRole("heading", { name: "Explore" })).toBeVisible();
});
test("admin can create, disable, reset and delete a user", async ({ page }) => {
  await login(page, "admin", "admin");
  await page.goto("/admin/users");
  await page.getByRole("button", { name: "Add member", exact: true }).click();
  const create = page.getByRole("dialog");
  await create.getByLabel("Username", { exact: true }).fill("browser_member");
  await create.getByLabel("Initial password").fill("test-member-123");
  await create.getByRole("button", { name: "Create account" }).click();
  await expect(create).toHaveCount(0);
  await page.getByLabel("Search usernames").fill("BROWSER_MEMBER");
  await expect(page).toHaveURL(/q=BROWSER_MEMBER/);
  const row = page.getByRole("row").filter({
    has: page.getByRole("button", { name: "Manage browser_member" }),
  });
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: "Manage browser_member" }).click();
  await page.getByRole("menuitem", { name: "Disable account" }).click();
  await expect(
    row.getByRole("cell", { name: "Disabled", exact: true }),
  ).toBeVisible();
  await row.getByRole("button", { name: "Manage browser_member" }).click();
  await page.getByRole("menuitem", { name: "Reset password" }).click();
  const reset = page.getByRole("dialog");
  await reset.getByLabel("New password").fill("new-member-123");
  await reset
    .getByRole("button", { name: "Reset password", exact: true })
    .click();
  await expect(reset).toHaveCount(0);
  await expect(
    row.getByRole("button", { name: "Manage browser_member" }),
  ).toBeFocused();
  await row.getByRole("button", { name: "Manage browser_member" }).click();
  await page.getByRole("menuitem", { name: "Enable account" }).click();
  await expect(
    row.getByRole("cell", { name: "Active", exact: true }),
  ).toBeVisible();
  await row.getByRole("button", { name: "Manage browser_member" }).click();
  await page.getByRole("menuitem", { name: "Delete account" }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete", exact: true })
    .click();
  await expect(row).toHaveCount(0);
});
for (const type of ["course", "video"]) {
  test(`share, review, edit and delete a ${type}`, async ({ page }) => {
    const title = `Browser ${type} ${Date.now()}`;
    await login(page);
    await page.goto(`/share/item?type=${type}`);
    await page
      .getByLabel("Resource URL")
      .fill(`https://example.com/browser-${type}-${Date.now()}`);
    await page.getByLabel("Title", { exact: true }).fill(title);
    await page
      .getByLabel("What will people learn?", { exact: true })
      .fill("A practical guide with clear examples.");
    await page
      .getByRole("button", { name: /^Share (article|course|video)$/ })
      .click();
    await expect(page).toHaveURL(new RegExp(`/explore/${type}s/\\d+$`));
    await expect(
      page.getByRole("heading", { name: title, exact: true }),
    ).toBeVisible();
    if (type === "course") {
      await expect(page.getByRole("status")).toHaveText(
        "Course shared. Add it to My learning when you’re ready.",
      );
      await page.route(
        "**/api/tracking",
        (route) =>
          route.fulfill({
            status: 503,
            json: { detail: "Please retry tracking" },
          }),
        { times: 1 },
      );
      await page
        .getByRole("button", { name: "Add to My learning", exact: true })
        .click();
      await expect(page.getByRole("alert")).toContainText(
        "Please retry tracking",
      );
      await expect(
        page.getByRole("heading", { name: title, exact: true }),
      ).toBeVisible();
      await page
        .getByRole("button", { name: "Add to My learning", exact: true })
        .click();
      await expect(page.getByRole("status")).toHaveText(
        "Added to My learning · Interested",
      );
    }
    if (type === "video")
      await expect(page.getByLabel("Your progress")).toHaveCount(0);
    await page
      .getByLabel("Your experience")
      .fill("Helpful and well explained.");
    await page
      .getByRole("button", { name: "Share review", exact: true })
      .click();
    await expect(page.getByText("Your change has been saved.")).toBeVisible();
    await page.getByRole("link", { name: "Edit", exact: true }).click();
    await page
      .getByLabel("Why do you recommend it?", { exact: false })
      .fill("Start here for a practical introduction.");
    await page.getByRole("button", { name: "Save changes" }).click();
    await expect(
      page.getByText("Start here for a practical introduction.", {
        exact: true,
      }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Delete", exact: true }).click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Delete", exact: true })
      .click();
    await expect(page.getByRole("heading", { name: "Explore" })).toBeVisible();
  });
}
test("a recoverable publish error preserves the form", async ({ page }) => {
  await login(page);
  await page.goto("/share/item?type=article");
  await page.getByLabel("Resource URL").fill("https://example.com/retry");
  await page.getByLabel("Title", { exact: true }).fill("Keep my draft");
  await page.route(
    "**/api/articles",
    (route) =>
      route.fulfill({
        status: 503,
        json: { message: "Please try again in a moment." },
      }),
    { times: 1 },
  );
  await page
    .getByRole("button", { name: /^Share (article|course|video)$/ })
    .click();
  await expect(page.getByRole("alert")).toContainText("Please try again");
  await expect(page.getByLabel("Title", { exact: true })).toHaveValue(
    "Keep my draft",
  );
  await page
    .getByRole("button", { name: /^Share (article|course|video)$/ })
    .click();
  await expect(
    page.getByRole("heading", { name: "Keep my draft" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete", exact: true })
    .click();
  await expect(page.getByRole("heading", { name: "Explore" })).toBeVisible();
});
for (const width of [390, 768, 1440])
  test(`responsive layout ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    await login(page);
    for (const route of [
      "/home",
      "/explore",
      "/activity",
      "/explore/paths/1",
    ]) {
      await page.goto(route);
      await expect(page.locator("h1")).toBeVisible();
      await expect(page.getByRole("status", { name: /Loading/ })).toHaveCount(
        0,
      );
      await page.evaluate(() => document.fonts.ready);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBe(true);
      await page.screenshot({
        path: `test-results/layout-${width}-${route.replaceAll("/", "-")}.png`,
        fullPage: true,
      });
    }
    if (width === 390) {
      await page.getByRole("button", { name: "Open navigation" }).click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page
        .getByRole("dialog")
        .getByRole("link", { name: "Explore", exact: true })
        .click();
      await expect(
        page.getByRole("heading", { name: "Explore" }),
      ).toBeVisible();
    }
  });
