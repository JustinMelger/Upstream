import { expect, type Page, test } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Username", { exact: true }).fill("alex");
  await page.getByLabel("Password", { exact: true }).fill("learn-demo-123");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "My learning", exact: true }),
  ).toBeVisible();
}

const suggestion = {
  title: "Page-authored title",
  description: "A useful page description.",
  suggested_provider: "Learning Docs",
};
test("fetched details update the preview and survive draft recovery", async ({
  page,
}) => {
  await login(page);
  await page.goto("/share/item?type=course");
  let calls = 0;
  await page.route("**/api/url-preview/metadata", async (route) => {
    calls++;
    await route.fulfill({ json: suggestion });
  });
  await page.getByLabel("Resource URL").fill("https://example.com/metadata");
  await page
    .getByRole("button", { name: "Fetch details", exact: true })
    .click();
  await expect(
    page.getByText("Details added. Review them before sharing."),
  ).toBeVisible();
  await expect(page.getByLabel("Title", { exact: true })).toHaveValue(
    suggestion.title,
  );
  await expect(
    page
      .getByRole("complementary", { name: "Publication preview" })
      .getByRole("heading", { name: suggestion.title }),
  ).toBeVisible();
  await expect(
    page.getByText("Draft saved in this tab", { exact: true }),
  ).toBeVisible();
  await page.reload();
  await page
    .getByRole("button", { name: "Restore draft", exact: true })
    .click();
  await expect(page.getByLabel("Title", { exact: true })).toHaveValue(
    suggestion.title,
  );
  await expect(page.getByLabel("Resource URL")).toHaveValue(
    "https://example.com/metadata",
  );
  await page.getByText("Additional details", { exact: false }).first().click();
  await expect(page.getByLabel("Provider", { exact: true })).toHaveValue(
    "Learning Docs",
  );
  expect(calls).toBe(1);
});
test("manual publication remains usable after fetching fails", async ({
  page,
}) => {
  await login(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/share/item?type=article");
  await page.route("**/api/url-preview/metadata", (route) =>
    route.fulfill({ status: 502, json: { message: "metadata_fetch_failed" } }),
  );
  const title = `Metadata recovery ${Date.now()}`;
  await page
    .getByLabel("Resource URL")
    .fill(`https://example.com/${Date.now()}`);
  await page
    .getByRole("button", { name: "Fetch details", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText(
    "You can enter them yourself.",
  );
  await page.getByLabel("Title", { exact: true }).fill(title);
  await page
    .getByRole("button", { name: "Share article", exact: true })
    .click();
  await expect(page).toHaveURL(/\/explore\/articles\/\d+$/);
  await page.getByRole("link", { name: "Edit", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Fetch details", exact: true }),
  ).toHaveCount(0);
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
test("changed URL and type discard late suggestions", async ({ page }) => {
  await login(page);
  await page.goto("/share/item?type=video");
  let release!: () => void;
  const delayed = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/url-preview/metadata", async (route) => {
    await delayed;
    await route.fulfill({ json: suggestion }).catch(() => {});
  });
  await page.getByLabel("Resource URL").fill("https://example.com/first");
  await page
    .getByRole("button", { name: "Fetch details", exact: true })
    .click();
  await page.getByLabel("Resource URL").fill("https://example.com/second");
  await page.getByRole("button", { name: "Article", exact: true }).click();
  release();
  await expect(page.getByLabel("Title", { exact: true })).toHaveValue("");
  await page.getByRole("button", { name: "Path", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Fetch details", exact: true }),
  ).toHaveCount(0);
});
