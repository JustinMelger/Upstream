import "@testing-library/jest-dom/vitest";
import { useRef } from "react";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { useMetadata } from "./metadata";
import { api } from "../lib/api/client";
vi.mock("../lib/api/client", () => ({ api: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});
function Form({ applied = () => {} }: { applied?: () => void }) {
  const ref = useRef<HTMLFormElement>(null);
  const metadata = useMetadata(ref, applied);
  return (
    <form
      ref={ref}
      onInput={(e) => metadata.changed((e.target as HTMLInputElement).name)}
    >
      <input name="url" aria-label="URL" defaultValue="https://example.com" />
      <input name="title" aria-label="Title" />
      <textarea name="description" aria-label="Description" />
      <input name="provider" aria-label="Provider" />
      <button
        type="button"
        disabled={metadata.pending}
        onClick={() => void metadata.fetchDetails()}
      >
        Fetch
      </button>
      <button type="button" onClick={metadata.cancel}>
        Discard
      </button>
      <p role="status">{metadata.message}</p>
      <p role="alert">{metadata.error}</p>
    </form>
  );
}
function deferred() {
  let resolve!: (value: unknown) => void;
  const promise = new Promise((r) => {
    resolve = r;
  });
  vi.mocked(api).mockReturnValue(promise);
  return resolve;
}
const details = {
  title: "Suggested",
  description: "Useful summary",
  suggested_provider: "Docs",
};
it("fills only untouched empty fields and updates draft/preview once", async () => {
  const resolve = deferred(),
    applied = vi.fn();
  render(<Form applied={applied} />);
  fireEvent.input(screen.getByLabelText("Provider"), {
    target: { value: "Mine" },
  });
  fireEvent.click(screen.getByText("Fetch"));
  fireEvent.click(screen.getByText("Fetch"));
  fireEvent.input(screen.getByLabelText("Title"), {
    target: { value: "Typing" },
  });
  fireEvent.input(screen.getByLabelText("Title"), { target: { value: "" } });
  await act(async () => resolve(details));
  expect(screen.getByLabelText("Title")).toHaveValue("");
  expect(screen.getByLabelText("Provider")).toHaveValue("Mine");
  expect(screen.getByLabelText("Description")).toHaveValue("Useful summary");
  expect(api).toHaveBeenCalledTimes(1);
  expect(applied).toHaveBeenCalledTimes(1);
});
it.each(["URL", "Discard", "unmount"])(
  "ignores stale responses after %s",
  async (action) => {
    const resolve = deferred(),
      applied = vi.fn();
    const view = render(<Form applied={applied} />);
    fireEvent.click(screen.getByText("Fetch"));
    if (action === "URL")
      fireEvent.input(screen.getByLabelText("URL"), {
        target: { value: "https://new.example" },
      });
    else if (action === "Discard") fireEvent.click(screen.getByText("Discard"));
    else view.unmount();
    await act(async () => resolve(details));
    expect(applied).not.toHaveBeenCalled();
    expect(vi.mocked(api).mock.calls[0][1]?.signal?.aborted).toBe(true);
  },
);
it("supports retry and distinguishes no metadata from preserved values", async () => {
  vi.mocked(api)
    .mockRejectedValueOnce(new Error())
    .mockResolvedValueOnce({})
    .mockResolvedValueOnce(details);
  render(<Form />);
  await act(async () => fireEvent.click(screen.getByText("Fetch")));
  expect(screen.getByRole("alert")).toHaveTextContent(
    "We couldn’t fetch details",
  );
  await act(async () => fireEvent.click(screen.getByText("Fetch")));
  expect(screen.getByRole("status")).toHaveTextContent("No usable details");
  for (const name of ["Title", "Description", "Provider"])
    fireEvent.input(screen.getByLabelText(name), { target: { value: "Mine" } });
  await act(async () => fireEvent.click(screen.getByText("Fetch")));
  expect(screen.getByRole("status")).toHaveTextContent(
    "existing fields were preserved",
  );
});
it("rejects invalid URLs without requesting", async () => {
  render(<Form />);
  fireEvent.input(screen.getByLabelText("URL"), {
    target: { value: "javascript:alert(1)" },
  });
  await act(async () => fireEvent.click(screen.getByText("Fetch")));
  expect(api).not.toHaveBeenCalled();
  expect(screen.getByRole("alert")).toHaveTextContent("valid HTTP or HTTPS");
});
