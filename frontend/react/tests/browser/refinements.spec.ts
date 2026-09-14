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

test("drafts restore after reload, stay separate by type, and clear on logout", async ({
  page,
}) => {
  await login(page);
  await page.goto("/share/item?type=article");
  await page.getByLabel("Title", { exact: true }).fill("An unfinished idea");
  await page.getByLabel("Resource URL").fill("https://example.com/draft");
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Restore draft", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Restore draft", exact: true })
    .click();
  await expect(page.getByLabel("Title", { exact: true })).toHaveValue(
    "An unfinished idea",
  );
  await page.getByRole("button", { name: "Video", exact: true }).click();
  await expect(page.getByLabel("Title", { exact: true })).toHaveValue("");
  await page.getByRole("button", { name: "Article", exact: true }).click();
  await page
    .getByRole("button", { name: "Restore draft", exact: true })
    .click();
  await expect(page.getByLabel("Title", { exact: true })).toHaveValue(
    "An unfinished idea",
  );
  await page.getByRole("button", { name: "Account menu" }).click();
  await page.getByRole("menuitem", { name: "Sign out" }).click();
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () =>
        Object.keys(sessionStorage).filter((k) =>
          k.startsWith("learning:draft:v1:"),
        ).length,
    ),
  ).toBe(0);
});
test("inline course progress fails locally then persists with compact mobile learning", async ({
  page,
}) => {
  await login(page);
  await page.goto("/explore/courses/1");
  if (
    await page
      .getByRole("button", { name: "Add to My learning", exact: true })
      .isVisible()
  )
    await page
      .getByRole("button", { name: "Add to My learning", exact: true })
      .click();
  await page
    .getByRole("button", { name: "Production-ready Python: course progress" })
    .click();
  await page
    .getByRole("menuitemradio", { name: "in progress", exact: true })
    .click();
  await expect(
    page.getByRole("button", {
      name: "Production-ready Python: course progress",
    }),
  ).toContainText("in progress");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/home");
  const title = page.getByRole("link", {
    name: "Production-ready Python",
    exact: true,
  });
  await expect(title).toBeVisible();
  expect((await title.boundingBox())!.y).toBeLessThan(844);
  const progress = page.getByLabel("Production-ready Python: course progress", {
    exact: true,
  });
  await page.route(
    "**/api/tracking",
    (route) =>
      route.fulfill({ status: 503, json: { message: "Please retry." } }),
    { times: 1 },
  );
  await progress.click();
  await page
    .getByRole("menuitemradio", { name: "completed", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText(
    "previous status is unchanged",
  );
  await expect(progress).toContainText("in progress");
  await progress.click();
  await page
    .getByRole("menuitemradio", { name: "completed", exact: true })
    .click();
  await expect(progress).toHaveCount(0);
  await page.getByRole("link", { name: /^Completed / }).click();
  await page.reload();
  await expect(
    page.getByLabel("Production-ready Python: course progress", {
      exact: true,
    }),
  ).toContainText("completed");
});
test("mobile filter drawer applies and cancels and catalog context survives detail", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await page.goto("/explore");
  await page.getByRole("button", { name: "Filters", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("combobox", { name: "Sort", exact: true })
    .selectOption("title");
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  expect(page.url()).not.toContain("sort=title");
  await page.getByRole("button", { name: "Filters", exact: true }).click();
  await page
    .getByRole("button", { name: "Provider: All", exact: true })
    .click();
  const options = page.getByLabel("Provider options", { exact: true });
  await expect(options.locator("option")).not.toHaveCount(1);
  const value = await options
    .locator("option:not([disabled])")
    .first()
    .getAttribute("value");
  await options.selectOption(value!);
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(
    page.getByRole("button", { name: /Remove provider filter/ }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Remove provider filter/ }).click();
  await page
    .getByRole("textbox", { name: "Search learning" })
    .fill("Production");
  await expect(page).toHaveURL(/q=Production/);
  await page
    .getByRole("link", { name: "Production-ready Python", exact: true })
    .click();
  await page.getByRole("link", { name: "Back to Explore" }).click();
  await expect(
    page.getByRole("textbox", { name: "Search learning" }),
  ).toHaveValue("Production");
});
test("validation focuses the first invalid field and review action focuses the form", async ({
  page,
}) => {
  await login(page);
  await page.goto("/share/item?type=article");
  await page
    .getByRole("button", { name: /^Share (article|course|video)$/ })
    .click();
  await expect(page.getByRole("alert")).toContainText("highlighted fields");
  await expect(
    page.getByRole("textbox", { name: /Resource URL/ }),
  ).toBeFocused();
  await page.goto("/explore/courses/1");
  await page
    .getByRole("button", { name: /^(Write a review|Edit your review)$/ })
    .click();
  await expect(page.getByLabel("Your experience")).toBeFocused();
});

test("an expired session retains the draft for the same account", async ({
  page,
}) => {
  await login(page);
  await page.goto("/share/item?type=article");
  await page.getByLabel("Title", { exact: true }).fill("After sign-in");
  await page
    .getByLabel("Resource URL")
    .fill("https://example.com/expired-draft");
  await page.route(
    "**/api/articles",
    (route) =>
      route.fulfill({ status: 401, json: { message: "unauthorized" } }),
    { times: 1 },
  );
  await page
    .getByRole("button", { name: /^Share (article|course|video)$/ })
    .click();
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Username", { exact: true }).fill("alex");
  await page.getByLabel("Password", { exact: true }).fill("learn-demo-123");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page
    .getByRole("button", { name: "Restore draft", exact: true })
    .click();
  await expect(page.getByLabel("Title", { exact: true })).toHaveValue(
    "After sign-in",
  );
});
test("restored path drafts retain removable references when an item was deleted", async ({
  page,
}) => {
  await login(page);
  const session = await (
    await page.request.get("/api/auth/browser/session")
  ).json();
  const headers = {
    Origin: "http://127.0.0.1:15173",
    "X-CSRF-Token": session.csrf_token,
  };
  const article = await page.request.post("/api/articles", {
    headers,
    data: {
      title: "Temporary draft reference",
      url: "https://example.com/draft-reference",
    },
  });
  expect(article.ok()).toBeTruthy();
  const id = (await article.json()).id;
  await page.goto("/share/path");
  await page.getByLabel("Path name").fill("Recoverable path draft");
  await page.getByLabel("Item type").selectOption("article");
  await page
    .getByLabel("Find learning items")
    .fill("Temporary draft reference");
  await page.getByRole("button", { name: "Add", exact: true }).click();
  await page.reload();
  await page
    .getByRole("button", { name: "Restore draft", exact: true })
    .click();
  expect(
    (await page.request.delete(`/api/articles/${id}`, { headers })).ok(),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Share path", exact: true }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByLabel("Path name")).toHaveValue(
    "Recoverable path draft",
  );
  await page
    .getByRole("button", {
      name: "Remove Temporary draft reference",
      exact: true,
    })
    .click();
  await expect(page.locator("ol li")).toHaveCount(0);
});
