import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { api, send } from "../lib/api/client";
import { Profile } from "./profile";

const auth = vi.hoisted(() => ({ expireSession: vi.fn() }));

vi.mock("./auth", () => ({
  useAuth: () => ({
    user: { username: "alex", role: "user" },
    expireSession: auth.expireSession,
  }),
}));

vi.mock("../lib/api/client", async (original) => ({
  ...(await original<typeof import("../lib/api/client")>()),
  api: vi.fn(),
  send: vi.fn(),
}));

function Location() {
  const location = useLocation();

  return (
    <output data-testid="location">
      {location.pathname + location.search}
    </output>
  );
}

function tree() {
  return (
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <MemoryRouter initialEntries={["/profile"]}>
        <Profile />
        <Location />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  auth.expireSession.mockReset();
  vi.mocked(send).mockReset();
  vi.mocked(api).mockImplementation(async (path) => {
    if (path === "/learning/summary") {
      return {
        in_progress: 1,
        completed: 2,
        selected_paths: 3,
        contributions: 4,
      };
    }

    return { items: [], total: 0, page: 1, page_size: 3 };
  });
});

afterEach(() => vi.restoreAllMocks());

function openDialog() {
  fireEvent.click(screen.getByRole("button", { name: "Change password" }));
}

function passwordDialog() {
  return screen.getByRole("dialog", { name: "Change password" });
}

function fillPasswords({
  current = "old-password",
  next = "new-password",
  confirmation = next,
}: {
  current?: string;
  next?: string;
  confirmation?: string;
} = {}) {
  const dialog = passwordDialog();
  fireEvent.change(within(dialog).getByLabelText("Current password"), {
    target: { value: current },
  });
  fireEvent.change(within(dialog).getByLabelText("New password"), {
    target: { value: next },
  });
  fireEvent.change(within(dialog).getByLabelText("Confirm new password"), {
    target: { value: confirmation },
  });
}

it("opens an accessible password-change dialog", () => {
  render(tree());
  openDialog();

  const dialog = passwordDialog();
  expect(dialog).toBeVisible();
  expect(within(dialog).getByLabelText("Current password")).toBeVisible();
  expect(within(dialog).getByLabelText("New password")).toBeVisible();
  expect(within(dialog).getByLabelText("Confirm new password")).toBeVisible();
});

it("shows a local error without submitting mismatched new passwords", () => {
  render(tree());
  openDialog();
  fillPasswords({ confirmation: "different-password" });
  fireEvent.click(
    within(passwordDialog()).getByRole("button", { name: "Change password" }),
  );

  expect(screen.getByRole("alert")).toHaveTextContent(
    "The new passwords do not match.",
  );
  expect(send).not.toHaveBeenCalled();
});

it("explains the new-password policy without submitting", () => {
  render(tree());
  openDialog();
  fillPasswords({ next: "short" });
  fireEvent.click(
    within(passwordDialog()).getByRole("button", { name: "Change password" }),
  );

  expect(screen.getByRole("alert")).toHaveTextContent(
    "Your new password must contain at least 12 characters.",
  );
  expect(send).not.toHaveBeenCalled();
});

it("changes the password, expires the session, and returns to login", async () => {
  vi.mocked(send).mockResolvedValue({ updated: 1 });
  render(tree());
  openDialog();
  fillPasswords();
  fireEvent.click(
    within(passwordDialog()).getByRole("button", { name: "Change password" }),
  );

  await waitFor(() =>
    expect(send).toHaveBeenCalledWith("/auth/password/change", {
      current_password: "old-password",
      new_password: "new-password",
    }),
  );
  expect(auth.expireSession).toHaveBeenCalledOnce();
  await waitFor(() =>
    expect(screen.getByTestId("location")).toHaveTextContent(
      "/login?passwordChanged=1",
    ),
  );
});

it("keeps entered passwords available after a failed request", async () => {
  vi.mocked(send).mockRejectedValue(
    new Error("The current password is incorrect."),
  );
  render(tree());
  openDialog();
  fillPasswords();
  fireEvent.click(
    within(passwordDialog()).getByRole("button", { name: "Change password" }),
  );

  await waitFor(() =>
    expect(screen.getByRole("alert")).toHaveTextContent(
      "The current password is incorrect.",
    ),
  );
  const dialog = passwordDialog();
  expect(within(dialog).getByLabelText("Current password")).toHaveValue(
    "old-password",
  );
  expect(within(dialog).getByLabelText("New password")).toHaveValue(
    "new-password",
  );
  expect(
    within(dialog).getByRole("button", { name: "Change password" }),
  ).toBeEnabled();
});
