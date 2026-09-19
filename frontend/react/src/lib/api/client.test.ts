import { afterEach, describe, expect, it, vi } from "vitest";

import { api, ApiError, externalUrl, safeReturn, setCsrf } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
  setCsrf("");
});
describe("browser API boundary", () => {
  it("normalizes legacy content IDs while preserving account and event identifiers", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            path_id: "12",
            colleague_id: "123",
            items: [{ id: "4", event_id: "review:4" }],
          }),
        ),
      ),
    );
    expect(await api("/paths/12/select")).toEqual({
      path_id: 12,
      colleague_id: "123",
      items: [{ id: 4, event_id: "review:4" }],
    });
  });
  it("sends cookies and CSRF without exposing credentials in persistent storage", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetch);
    setCsrf("csrf-proof");
    await api("/tracking", { method: "POST", body: "{}" });
    expect(fetch).toHaveBeenCalledWith(
      "/api/tracking",
      expect.objectContaining({
        credentials: "same-origin",
        headers: expect.objectContaining({ "X-CSRF-Token": "csrf-proof" }),
      }),
    );
  });
  it("expires client authentication on a rejected session", async () => {
    const listener = vi.fn();
    window.addEventListener("session-expired", listener);
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response('{"message":"unauthorized"}', { status: 401 }),
        ),
    );
    await expect(api("/learning/summary")).rejects.toBeInstanceOf(ApiError);
    expect(listener).toHaveBeenCalledOnce();
    window.removeEventListener("session-expired", listener);
  });
  it("turns structured validation details into a useful message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: [
              {
                loc: ["body", "new_password"],
                msg: "Value error, password must contain at least 12 characters",
              },
            ],
          }),
          { status: 422 },
        ),
      ),
    );

    await expect(api("/auth/password/change")).rejects.toMatchObject({
      status: 422,
      message: "password must contain at least 12 characters",
    });
  });
  it.each([
    "https://evil.example",
    "//evil.example",
    "/\\evil.example",
    "/login",
    "/home\n",
  ])("rejects unsafe return URL %s", (value) => {
    expect(safeReturn(value)).toBe("/home");
  });
  it("preserves internal detail and review deep links", () =>
    expect(safeReturn("/explore/courses/2?view=reviews")).toBe(
      "/explore/courses/2?view=reviews",
    ));
  it("rejects executable external URLs", () => {
    expect(externalUrl("javascript:alert(1)")).toBeUndefined();
    expect(externalUrl("https://example.com")).toBe("https://example.com/");
  });
});
