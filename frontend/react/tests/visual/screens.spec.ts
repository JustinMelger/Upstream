import { test, expect } from "@playwright/test";

const items = [
  {
    id: 1,
    type: "course",
    title: "Designing reliable systems",
    url: "https://example.com/course",
    description:
      "Build a practical understanding of resilient services, clear boundaries, and thoughtful trade-offs.",
    provider: "Learning Lab",
    level: "Intermediate",
    duration_hours: 4,
    created_by: "maya",
    rating: 4.5,
    review_count: 2,
    status: "in_progress",
    recommendation_note: "The examples made distributed systems click.",
  },
  {
    id: 2,
    type: "article",
    title: "Small habits for better code reviews",
    description:
      "A thoughtful guide to feedback that helps people and their work grow.",
    provider: "Engineering Notes",
    created_by: "sam",
    rating: 5,
    review_count: 1,
  },
  {
    id: 3,
    type: "video",
    title: "Making complex ideas feel simple",
    description:
      "Clear examples and visual explanations for your next technical presentation.",
    created_by: "alex",
    review_count: 0,
  },
  {
    id: 4,
    type: "path",
    title: "A foundation for thoughtful engineering",
    description:
      "A short, mixed collection to build confidence in everyday engineering decisions.",
    created_by: "maya",
    review_count: 3,
    rating: 4.7,
  },
];
const summary = {
  interested: 3,
  in_progress: 2,
  completed: 8,
  selected_paths: 1,
  contributions: 4,
  next_course: {
    id: 1,
    title: items[0].title,
    provider: "Learning Lab",
    duration_hours: 4,
    status: "in_progress",
    url: "https://example.com/course",
  },
};
const pageOf = (data: unknown[]) => ({
  items: data,
  total: data.length,
  page: 1,
  page_size: 24,
});

for (const width of [390, 768, 1440]) {
  for (const screen of [
    "home",
    "explore",
    "activity",
    "detail",
    "article-detail",
    "video-detail",
    "path-detail",
    "activity-personal",
    "activity-stats",
    "profile",
    "admin",
    "admin-dialog",
    "journey-added",
    "journey-completed",
    "journey-start",
    "empty",
    "error",
    "loading",
    "share",
    "metadata-filled",
    "metadata-error",
    "fallback",
  ]) {
    test(`${screen} at ${width}px`, async ({ page }) => {
      const journey = screen.startsWith("journey-");
      let journeyStatus: string | null =
        screen === "journey-completed" ? "in_progress" : null;
      await page.setViewportSize({ width, height: 1000 });
      await page.route("http://127.0.0.1:15174/api/**", async (route) => {
        const path = new URL(route.request().url()).pathname.slice(4);
        let body: unknown;
        if (path === "/url-preview/metadata") {
          if (screen === "metadata-error")
            return route.fulfill({
              status: 502,
              json: { message: "metadata_fetch_failed" },
            });
          body = {
            title: "Small habits for better code reviews",
            description:
              "A thoughtful guide to feedback that helps people and their work grow.",
            suggested_provider: "Engineering Notes",
          };
        } else if (path === "/auth/browser/session")
          body = {
            username: "alex",
            role: screen.startsWith("admin") ? "admin" : "user",
            expires_at: "2030-01-01T00:00:00Z",
            csrf_token: "visual-test",
          };
        else if (path === "/tracking") {
          journeyStatus = route.request().postDataJSON().status;
          body = { course_id: 1, status: journeyStatus };
        } else if (path === "/learning/summary")
          body = journey
            ? {
                ...summary,
                in_progress: Number(journeyStatus === "in_progress"),
                interested: Number(journeyStatus === "interested"),
                completed: Number(journeyStatus === "completed"),
                next_course:
                  journeyStatus === "completed"
                    ? null
                    : { ...summary.next_course, status: journeyStatus },
              }
            : summary;
        else if (path === "/learning/items")
          body =
            new URL(route.request().url()).searchParams.get("view") === "paths"
              ? pageOf([
                  {
                    ...items[3],
                    status: "in_progress",
                    course_progress: { completed: 2, total: 4 },
                  },
                ])
              : journey
                ? pageOf(
                    journeyStatus &&
                      (!new URL(route.request().url()).searchParams.get(
                        "status",
                      ) ||
                        new URL(route.request().url()).searchParams.get(
                          "status",
                        ) === journeyStatus)
                      ? [{ ...items[0], status: journeyStatus }]
                      : [],
                  )
                : screen === "profile"
                  ? {
                      ...pageOf(
                        items
                          .slice(0, 3)
                          .map((item) => ({ ...item, created_by: "alex" })),
                      ),
                      page_size: 3,
                    }
                  : pageOf([items[0]]);
        else if (path === "/catalog") {
          if (screen === "loading") return;
          if (screen === "error")
            return route.fulfill({
              status: 503,
              json: {
                message:
                  "The library is temporarily unavailable. Please try again.",
              },
            });
          body = pageOf(screen === "empty" ? [] : items);
        } else if (path === "/activity")
          body = pageOf(
            [
              {
                event_id: "review:course:1",
                event_type: "review",
                type: "course",
                content_id: 1,
                title: items[0].title,
                actor: "maya",
                happened_at: "2026-09-09T09:00:00Z",
                rating: 5,
                excerpt:
                  "Practical examples and a clear structure. A useful place to start.",
                excerpt_kind: "review",
              },
              {
                event_id: "share:article:2",
                event_type: "share",
                type: "article",
                content_id: 2,
                title: items[1].title,
                actor: "sam",
                happened_at: "2026-09-08T09:00:00Z",
                excerpt:
                  "A thoughtful guide to feedback that helps people and their work grow.",
                excerpt_kind: "description",
              },
            ].filter(
              (event) =>
                screen !== "activity-personal" || event.event_type === "review",
            ),
          );
        else if (path === "/auth/users")
          body = [
            { username: "alex", role: "admin", disabled: false },
            { username: "maya", role: "user", disabled: false },
            { username: "sam", role: "user", disabled: false },
            { username: "jordan", role: "user", disabled: true },
          ];
        else if (path === "/articles/2")
          body = {
            ...items[1],
            url: "https://example.com/article",
            recommendation_note:
              "This helped our reviews become conversations. Start with asking better questions.",
          };
        else if (path === "/videos/3")
          body = { ...items[2], url: "https://example.com/video" };
        else if (path === "/paths/4")
          body = {
            ...items[3],
            name: items[3].title,
            recommendation_note:
              "A thoughtful route through the technical and human sides of engineering.",
            items: [
              items[0],
              items[1],
              items[2],
              { ...items[0], id: 5, title: "Practical architecture" },
            ],
          };
        else if (path === "/learning/paths/4")
          body = {
            selected: true,
            status: "in_progress",
            completed: 1,
            total: 2,
            courses: [
              { id: 1, status: "in_progress" },
              { id: 5, status: "completed" },
            ],
          };
        else if (path === "/courses/1")
          body = {
            ...items[0],
            url: "https://example.com/course",
            recommendation_note:
              "The examples helped me connect architecture decisions to the problems we actually face. Start with the first two chapters.",
            category: "Engineering",
            language: "English",
          };
        else if (path === "/videos/3/reviews") body = [];
        else if (/^\/(courses|articles|paths)\/\d+\/reviews$/.test(path))
          body = [
            {
              id: 1,
              rating: 5,
              text: "Practical examples and a clear structure. A useful place to start.",
              created_by: "sam",
              created_at: "2026-09-08T09:00:00Z",
            },
          ];
        else throw new Error(`Unmocked visual request: ${path}`);
        await route.fulfill({ json: body });
      });
      if (screen === "fallback")
        await page.route("**/artwork/**", (route) => route.abort());
      const supportingRoutes: Record<string, string> = {
        "metadata-filled": "/share/item?type=article",
        "metadata-error": "/share/item?type=article",
        "journey-added": "/explore/courses/1",
        "journey-completed": "/home",
        "journey-start": "/home",
        "article-detail": "/explore/articles/2",
        "video-detail": "/explore/videos/3",
        "path-detail": "/explore/paths/4",
        "activity-personal": "/activity",
        "activity-stats": "/activity?view=stats",
        admin: "/admin/users",
        "admin-dialog": "/admin/users",
      };
      const path =
        supportingRoutes[screen] ||
        (screen === "share"
          ? "/share/item?type=article"
          : screen === "fallback"
            ? "/explore"
            : screen === "detail"
              ? "/explore/courses/1"
              : ["empty", "error", "loading"].includes(screen)
                ? "/explore"
                : `/${screen}${screen === "activity" ? "?scope=shared" : ""}`);

      await page.goto(path);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      if (screen === "loading")
        await expect(
          page.getByRole("status", { name: /Loading/ }),
        ).toBeVisible();
      else {
        await expect(page.getByRole("status", { name: /Loading/ })).toHaveCount(
          0,
        );
        if (screen === "error")
          await expect(page.getByRole("alert")).toBeVisible();
      }
      if (screen.startsWith("metadata-")) {
        await page
          .getByLabel("Resource URL")
          .fill("https://example.com/code-reviews");
        await page
          .getByRole("button", { name: "Fetch details", exact: true })
          .click();
        await expect(
          page.getByText(
            screen === "metadata-error"
              ? "We couldn’t fetch details. You can enter them yourself."
              : "Details added. Review them before sharing.",
          ),
        ).toBeVisible();
        await expect(
          page.getByText("Draft saved in this tab", { exact: true }),
        ).toBeVisible();
      }
      if (screen === "journey-added") {
        await page
          .getByRole("button", { name: "Add to My learning", exact: true })
          .click();
        await expect(page.getByRole("status")).toHaveText(
          "Added to My learning · Interested",
        );
      }
      if (screen === "journey-completed") {
        await page
          .getByRole("button", { name: "Mark completed", exact: true })
          .click();
        await expect(page.getByRole("button", { name: "Undo" })).toBeEnabled();
        await expect(
          page.getByRole("heading", {
            name: "You’ve finished your in-progress courses.",
          }),
        ).toBeVisible();
      }
      if (screen === "journey-start") {
        await page.evaluate(() => {
          window.open = () => null;
        });
        await page
          .getByRole("region", { name: "Continue learning" })
          .getByRole("button", { name: "Start learning" })
          .click();
        await expect(
          page
            .getByRole("region", { name: "Learning update" })
            .getByRole("link", { name: "Open course" }),
        ).toBeVisible();
      }
      if (screen === "admin-dialog")
        await page
          .getByRole("button", { name: "Add member", exact: true })
          .click();
      if (screen === "share") {
        await page
          .getByLabel("Title", { exact: true })
          .fill("Small habits for better code reviews");
        await page
          .getByLabel("Resource URL")
          .fill("https://example.com/reviews");
        await page
          .getByLabel("What will people learn?", { exact: true })
          .fill(
            "Simple practices to make reviews kinder, clearer and more effective.",
          );
        await page
          .getByLabel(/Why do you recommend it/)
          .fill(
            "This helped our reviews become conversations. Start with the section on asking better questions.",
          );
        await expect(
          page.getByText("Draft saved in this tab", { exact: true }),
        ).toBeVisible();
        if (width < 900)
          await page.getByText("Preview your share", { exact: true }).click();
      }
      await page.evaluate(() => document.fonts.ready);
      await page.evaluate(async () => {
        await Promise.all(
          Array.from(document.images)
            .filter((img) => img.getClientRects().length > 0)
            .map((img) => {
              img.loading = "eager";
              return img.decode().catch(() => {});
            }),
        );
      });
      await expect(page).toHaveScreenshot(`${screen}-${width}.png`, {
        fullPage: true,
        animations: "disabled",
      });
    });
  }
}
