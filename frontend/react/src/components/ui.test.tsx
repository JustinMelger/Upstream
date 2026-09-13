import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Pagination, Confirm } from "./ui";
describe("shared interactions", () => {
  it("paginates inside a form without publishing it", async () => {
    const submit = vi.fn((e) => e.preventDefault()),
      change = vi.fn();
    render(
      <form onSubmit={submit}>
        <Pagination page={1} total={60} onChange={change} />
      </form>,
    );
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(change).toHaveBeenCalledWith(2);
    expect(submit).not.toHaveBeenCalled();
    expect(
      (screen.getByRole("button", { name: "Previous" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
  });
  it("requires confirmation and restores focus when cancelled", async () => {
    const remove = vi.fn();
    render(
      <Confirm
        title="Delete course?"
        description="Removes reviews and path references."
        onConfirm={remove}
        busy={false}
      >
        <button>Remove item</button>
      </Confirm>,
    );
    const trigger = screen.getByRole("button", { name: "Remove item" });
    await userEvent.click(trigger);
    expect(document.body.contains(screen.getByRole("dialog"))).toBe(true);
    expect(remove).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(document.activeElement).toBe(trigger);
    expect(remove).not.toHaveBeenCalled();
  });
});
