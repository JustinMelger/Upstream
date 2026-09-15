import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { expect, it, vi } from "vitest";

import { api } from "../../lib/api/client";
import { ItemPicker, type PathItem } from "./ItemPicker";

vi.mock("../../lib/api/client", async (original) => ({
  ...(await original<typeof import("../../lib/api/client")>()),
  api: vi.fn(),
}));

it("selects and adds all resource types inside a form that updates its preview on input", async () => {
  vi.mocked(api).mockImplementation(async (path) => {
    const type = new URL(String(path), "https://example.com").searchParams.get(
      "type",
    );

    return {
      items: [{ id: 1, type, title: `${type} resource` }],
      total: 1,
      page: 1,
      page_size: 6,
    } as never;
  });
  const user = userEvent.setup();

  function Editor() {
    const [revision, setRevision] = useState(0);
    const [items, setItems] = useState<PathItem[]>([]);

    return (
      <form onInput={() => setRevision((value) => value + 1)}>
        <output aria-label="Preview revision">{revision}</output>
        <ItemPicker
          selected={items}
          add={(item) => setItems((previous) => [...previous, item])}
        />
        <output aria-label="Sequence">
          {items.map((item) => item.type).join(",")}
        </output>
      </form>
    );
  }

  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <Editor />
    </QueryClientProvider>,
  );
  await screen.findByText("course resource");
  await user.click(screen.getByRole("button", { name: "Add" }));

  for (const type of ["article", "video"]) {
    await user.selectOptions(screen.getByLabelText("Item type"), type);
    expect(screen.getByLabelText("Item type")).toHaveValue(type);
    await screen.findByText(`${type} resource`);
    await user.click(screen.getByRole("button", { name: "Add" }));
  }

  expect(screen.getByLabelText("Sequence")).toHaveTextContent(
    "course,article,video",
  );
});
