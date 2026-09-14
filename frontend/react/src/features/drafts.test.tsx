import { act, cleanup, fireEvent, render } from "@testing-library/react";
import { useRef, useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { claimDrafts, clearDrafts, type DraftItem, useDraft } from "./drafts";

function Form({ identity = "article:new" }: { identity?: string }) {
  const ref = useRef<HTMLFormElement>(null);
  const [items, setItems] = useState<DraftItem[]>([]);
  const draft = useDraft("alice", identity, ref, items);

  return (
    <form ref={ref} onInput={draft.changed}>
      <input name="title" aria-label="Title" defaultValue="Published" />
      <button
        type="button"
        onClick={() => {
          draft.changed();
          setItems([{ type: "course", id: 1, title: "Course" }]);
        }}
      >
        Add course
      </button>
      {draft.candidate && (
        <button
          type="button"
          onClick={() => {
            const saved = draft.restore();
            if (saved) setItems(saved.items);
          }}
        >
          Restore draft
        </button>
      )}
      <button type="button" onClick={draft.complete}>
        Publish
      </button>
      <button type="button" onClick={draft.discard}>
        Discard
      </button>
      {draft.unavailable && <p role="status">Recovery unavailable</p>}
      <output>{items.length}</output>
    </form>
  );
}

const key = "learning:draft:v1:alice:article:new";
beforeEach(() => {
  vi.useFakeTimers();
  sessionStorage.clear();
  claimDrafts("alice");
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
  sessionStorage.clear();
});
describe("session draft recovery", () => {
  it("debounces writes and offers an explicit restore", () => {
    const view = render(<Form />);
    fireEvent.input(view.getByLabelText("Title"), {
      target: { value: "My draft" },
    });
    act(() => vi.advanceTimersByTime(499));
    expect(sessionStorage.getItem(key)).toBeNull();
    act(() => vi.advanceTimersByTime(1));
    expect(JSON.parse(sessionStorage.getItem(key)!).values.title).toBe(
      "My draft",
    );
    view.unmount();
    const reopened = render(<Form />);
    expect((reopened.getByLabelText("Title") as HTMLInputElement).value).toBe(
      "Published",
    );
    fireEvent.click(reopened.getByText("Restore draft"));
    expect((reopened.getByLabelText("Title") as HTMLInputElement).value).toBe(
      "My draft",
    );
  });
  it("flushes the latest text and items on navigation before the timer", () => {
    const view = render(<Form />);
    fireEvent.input(view.getByLabelText("Title"), {
      target: { value: "Last keystroke" },
    });
    fireEvent.click(view.getByText("Add course"));
    view.unmount();
    const saved = JSON.parse(sessionStorage.getItem(key)!);
    expect(saved.values.title).toBe("Last keystroke");
    expect(saved.items).toHaveLength(1);
  });
  it("does not resurrect a draft after publication", () => {
    const view = render(<Form />);
    fireEvent.input(view.getByLabelText("Title"), {
      target: { value: "Publish me" },
    });
    fireEvent.click(view.getByText("Publish"));
    view.unmount();
    act(() => vi.runAllTimers());
    expect(sessionStorage.getItem(key)).toBeNull();
  });
  it("clears pending saves on logout and account switches", () => {
    const view = render(<Form />);
    fireEvent.input(view.getByLabelText("Title"), {
      target: { value: "Private draft" },
    });
    clearDrafts();
    view.unmount();
    expect(sessionStorage.getItem(key)).toBeNull();
    claimDrafts("alice");
    sessionStorage.setItem(key, "draft");
    claimDrafts("bob");
    expect(sessionStorage.getItem(key)).toBeNull();
  });
  it("preserves drafts when the same user returns after expiry", () => {
    sessionStorage.setItem(key, "saved");
    claimDrafts("alice");
    expect(sessionStorage.getItem(key)).toBe("saved");
  });
  it("keeps edit and new identities separate", () => {
    const view = render(<Form identity="article:7" />);
    fireEvent.input(view.getByLabelText("Title"), {
      target: { value: "Edit draft" },
    });
    view.unmount();
    expect(sessionStorage.getItem(key)).toBeNull();
    expect(
      sessionStorage.getItem("learning:draft:v1:alice:article:7"),
    ).not.toBeNull();
  });
  it("keeps the form usable when storage writes fail", () => {
    const view = render(<Form />);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    fireEvent.input(view.getByLabelText("Title"), {
      target: { value: "Keep typing" },
    });
    act(() => vi.advanceTimersByTime(500));
    expect(view.getByText("Recovery unavailable").textContent).toBe(
      "Recovery unavailable",
    );
    expect((view.getByLabelText("Title") as HTMLInputElement).value).toBe(
      "Keep typing",
    );
  });
});
