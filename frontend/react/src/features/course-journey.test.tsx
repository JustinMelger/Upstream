import { fireEvent, render, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { beforeEach, afterEach, expect, it, vi } from "vitest";
import {
  CourseActions,
  CourseFeedback,
  CourseJourneyProvider,
} from "./course-journey";
import { send } from "../lib/api/client";
const auth = vi.hoisted(() => ({ username: "alex" }));
vi.mock("./auth", () => ({
  useAuth: () => ({ user: { username: auth.username } }),
}));
vi.mock("../lib/api/client", async (original) => ({
  ...(await original<typeof import("../lib/api/client")>()),
  send: vi.fn(),
}));
const course = {
  id: 1,
  title: "Reliable systems",
  status: "interested",
  url: "https://example.com/course",
};
function tree(status = "interested") {
  return (
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <MemoryRouter>
        <CourseJourneyProvider>
          <CourseFeedback />
          <CourseActions course={{ ...course, status }} />
        </CourseJourneyProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}
beforeEach(() => {
  auth.username = "alex";
  vi.mocked(send).mockReset();
});
afterEach(() => vi.restoreAllMocks());
it("reserves one tab immediately and navigates only after tracking succeeds", async () => {
  let resolve!: (value: unknown) => void;
  vi.mocked(send).mockImplementation(
    () =>
      new Promise((done) => {
        resolve = done;
      }),
  );
  const tab = {
    opener: {},
    document: { title: "", body: { textContent: "" } },
    closed: false,
    close: vi.fn(),
    location: { replace: vi.fn() },
  };
  const open = vi
    .spyOn(window, "open")
    .mockReturnValue(tab as unknown as Window);
  const view = render(tree());
  fireEvent.click(view.getByRole("button", { name: "Start learning" }));
  expect(open).toHaveBeenCalledTimes(1);
  expect(tab.opener).toBeNull();
  expect(tab.location.replace).not.toHaveBeenCalled();
  fireEvent.click(view.getByRole("button", { name: "Start learning" }));
  expect(send).toHaveBeenCalledTimes(1);
  resolve({});
  await waitFor(() =>
    expect(tab.location.replace).toHaveBeenCalledWith(course.url),
  );
  expect(send).toHaveBeenCalledWith("/tracking", {
    course_id: 1,
    status: "in_progress",
  });
});
it("closes the reserved tab on a failed save and keeps the prior status", async () => {
  const close = vi.fn();
  vi.spyOn(window, "open").mockReturnValue({
    opener: null,
    document: { body: {} },
    close,
  } as unknown as Window);
  vi.mocked(send).mockRejectedValue(new Error("Try later"));
  const view = render(tree());
  fireEvent.click(view.getByRole("button", { name: "Start learning" }));
  await waitFor(() => expect(close).toHaveBeenCalledOnce());
  expect(view.getByRole("alert").textContent).toContain(
    "previous status is unchanged",
  );
  expect(
    view.getByRole("button", { name: "Reliable systems: course progress" })
      .textContent,
  ).toContain("interested");
});
it("offers a manual resource link when the popup is blocked", async () => {
  vi.spyOn(window, "open").mockReturnValue(null);
  vi.mocked(send).mockResolvedValue({});
  const view = render(tree());
  fireEvent.click(view.getByRole("button", { name: "Start learning" }));
  await waitFor(() =>
    expect(
      view.getByRole("link", { name: "Open course" }).getAttribute("href"),
    ).toBe(course.url),
  );
  expect(view.getByRole("status").textContent).toBe("Added to In progress.");
});
it("completion offers Undo, retains it on failure, and restores the prior status", async () => {
  vi.mocked(send)
    .mockResolvedValueOnce({})
    .mockRejectedValueOnce(new Error("Try later"))
    .mockResolvedValueOnce({});
  const view = render(tree("in_progress"));
  fireEvent.click(view.getByRole("button", { name: "Mark completed" }));
  await waitFor(() =>
    expect(
      (view.getByRole("button", { name: "Undo" }) as HTMLButtonElement)
        .disabled,
    ).toBe(false),
  );
  fireEvent.click(view.getByRole("button", { name: "Undo" }));
  await waitFor(() =>
    expect(
      view.getByRole("region", { name: "Learning update" }).textContent,
    ).toContain("Try later"),
  );
  fireEvent.click(view.getByRole("button", { name: "Undo" }));
  await waitFor(() =>
    expect(view.getByRole("status").textContent).toContain("Completion undone"),
  );
  expect(vi.mocked(send).mock.calls.map((call) => call[1])).toEqual([
    { course_id: 1, status: "completed" },
    { course_id: 1, status: "in_progress" },
    { course_id: 1, status: "in_progress" },
  ]);
});
it("account switching clears in-memory feedback", async () => {
  vi.mocked(send).mockResolvedValue({});
  const view = render(tree("in_progress"));
  fireEvent.click(view.getByRole("button", { name: "Mark completed" }));
  await waitFor(() =>
    expect(view.getByRole("status").textContent).toContain("Course completed"),
  );
  auth.username = "sam";
  view.rerender(tree("in_progress"));
  expect(view.queryByRole("region", { name: "Learning update" })).toBeNull();
});
it("reopening completed courses does not reset tracking", () => {
  const view = render(tree("completed"));
  expect(
    view.getByRole("link", { name: "Open course" }).getAttribute("href"),
  ).toBe(course.url);
  expect(send).not.toHaveBeenCalled();
});
