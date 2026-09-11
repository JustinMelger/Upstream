import { test, expect, type Page } from "@playwright/test";
async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Username", { exact: true }).fill("alex");
  await page.getByLabel("Password", { exact: true }).fill("learn-demo-123");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "My learning", exact: true }),
  ).toBeVisible();
}
test("spotlight preserves unique bounded results and yields to URL filters and pagination", async ({
  page,
}) => {
  await login(page);
  const items = Array.from({ length: 25 }, (_, i) => ({
    id: i + 100,
    type: "article",
    title: `Discovery resource ${i + 1}`,
    description: "Useful ideas",
    recommendation_note: i === 1 ? "This made the topic click." : null,
    created_by: "maya",
    rating: 0,
    review_count: 0,
  }));
  const calls: string[] = [];
  await page.route("**/api/catalog?**", (route) => {
    const url = new URL(route.request().url());
    const p = Number(url.searchParams.get("page") || 1);
    const q = url.searchParams.get("q") || "";
    const filtered = items.filter((item) => item.title.includes(q));
    return route.fulfill({
      json: {
        items: filtered.slice((p - 1) * 24, p * 24),
        total: filtered.length,
        page: p,
        page_size: 24,
      },
    });
  });
  page.on("request", (request) => {
    if (new URL(request.url()).pathname.startsWith("/api/"))
      calls.push(new URL(request.url()).pathname);
  });
  await page.goto("/explore");
  const spotlight = page.getByRole("region", {
    name: "Recently shared spotlight",
  });
  await expect(spotlight).toContainText("Discovery resource 2");
  await expect(page.locator("[data-resource-id]")).toHaveCount(24);
  expect(
    await page
      .locator("[data-resource-id]")
      .evaluateAll(
        (nodes) =>
          new Set(nodes.map((node) => node.getAttribute("data-resource-id")))
            .size,
      ),
  ).toBe(24);
  const reads = calls.filter((path) => path !== "/api/auth/browser/session");
  expect(new Set(reads)).toEqual(new Set(["/api/catalog"]));
  expect(reads.length).toBeLessThanOrEqual(2); // StrictMode may cancel and retry the initial read.
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page).toHaveURL(/page=2/);
  await expect(spotlight).toHaveCount(0);
  await expect(page.locator("[data-resource-id]")).toHaveCount(1);
  await page.goBack();
  await expect(spotlight).toBeVisible();
  await page.getByLabel("Search learning").fill("Discovery resource 25");
  await expect(page).toHaveURL(/q=Discovery/);
  await expect(spotlight).toHaveCount(0);
  await expect(page.locator("[data-resource-id]")).toHaveCount(1);
  await page.getByRole("link", { name: "Clear all", exact: true }).click();
  await expect(spotlight).toBeVisible();
  await page
    .getByRole("combobox", { name: "Sort", exact: true })
    .selectOption("rating");
  await expect(spotlight).toHaveCount(0);
});
test("live share previews follow draft restore, discard, type changes and saved summaries", async ({
  page,
}) => {
  await login(page);
  await page.goto("/share/item?type=article");
  const preview = page.getByRole("complementary", {
    name: "Publication preview",
  });
  await page
    .getByLabel("Title", { exact: true })
    .fill("A preview worth sharing");
  await page
    .getByLabel("Resource URL")
    .fill("https://example.com/discovery-preview");
  await page
    .getByLabel("What will people learn?", { exact: true })
    .fill("Practice asking better questions.");
  await page
    .getByLabel(/Why do you recommend it/)
    .fill("This improved our conversations.");
  await expect(preview).toContainText("Practice asking better questions.");
  await expect(preview).toContainText("This improved our conversations.");
  await expect(
    page.getByText("Draft saved in this tab", { exact: true }),
  ).toBeVisible();
  const cover = await preview
    .locator("[data-artwork]")
    .getAttribute("data-artwork");
  await page.reload();
  await page
    .getByRole("button", { name: "Restore draft", exact: true })
    .click();
  await expect(preview).toContainText("A preview worth sharing");
  await expect(preview.locator("[data-artwork]")).toHaveAttribute(
    "data-artwork",
    cover!,
  );
  await page.getByRole("button", { name: "Path", exact: true }).click();
  await expect(page.getByLabel("Path name")).toHaveValue("");
  await expect(preview).toContainText("0 items");
  await page.getByRole("button", { name: "Article", exact: true }).click();
  await page
    .getByRole("button", { name: "Restore draft", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Share article", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "A preview worth sharing", level: 1 }),
  ).toBeVisible();
  await expect(page.locator("[data-artwork]")).toHaveAttribute(
    "data-artwork",
    cover!,
  );
  await page.getByRole("link", { name: "Edit", exact: true }).click();
  await expect(
    page.getByRole("textbox", { name: "What will people learn?", exact: true }),
  ).toHaveValue("Practice asking better questions.");
  await page.getByLabel("Title", { exact: true }).fill("A changed draft");
  await page
    .getByRole("button", { name: "Discard draft", exact: true })
    .click();
  await expect(preview).toContainText("A preview worth sharing");
  await page.getByRole("link", { name: "Cancel", exact: true }).click();
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Explore", exact: true }),
  ).toBeVisible();
});

test.afterEach(async ({ page }) => {
  const session = await page.request.get("/api/auth/browser/session");
  if (!session.ok()) return;
  const { csrf_token, username } = await session.json();
  if (username !== "alex") return;
  const result = await page.request.get(
    "/api/catalog?author=alex&type=article&q=preview",
  );
  if (!result.ok()) return;
  for (const item of (await result.json()).items) {
    if (item.url === "https://example.com/discovery-preview")
      await page.request.delete(`/api/articles/${item.id}`, {
        headers: {
          Origin: "http://127.0.0.1:15173",
          "X-CSRF-Token": csrf_token,
        },
      });
  }
});
