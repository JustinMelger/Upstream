import { useEffect, useRef, useState, type RefObject } from "react";
import { api } from "../lib/api/client";
import type { components } from "../lib/api/generated";

type Metadata = components["schemas"]["UrlPreviewMetadataResponse"];
export function useMetadata(
  form: RefObject<HTMLFormElement | null>,
  applied: () => void,
) {
  const request = useRef<AbortController | null>(null);
  const touched = useRef(new Set<string>());
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const field = (name: string) =>
    form.current?.elements.namedItem(name) as
      HTMLInputElement | HTMLTextAreaElement | null;
  function cancel() {
    request.current?.abort();
    request.current = null;
    setPending(false);
    setMessage("");
    setError("");
  }
  useEffect(() => () => request.current?.abort(), []);
  function changed(name: string) {
    touched.current.add(name);
    if (name === "url") cancel();
  }
  async function fetchDetails() {
    if (request.current) return;
    const url = field("url")?.value || "";
    try {
      const parsed = new URL(url);
      if (
        !["http:", "https:"].includes(parsed.protocol) ||
        parsed.username ||
        parsed.password
      )
        throw new Error();
    } catch {
      setError("Enter a valid HTTP or HTTPS resource URL first.");
      return;
    }
    const controller = new AbortController();
    request.current = controller;
    touched.current.clear();
    const names = ["title", "description", "provider"] as const;
    const empty = new Set(
      names.filter((name) => field(name) && !field(name)!.value.trim()),
    );
    setPending(true);
    setMessage("");
    setError("");
    try {
      const data = await api<Metadata>("/url-preview/metadata", {
        method: "POST",
        body: JSON.stringify({ url }),
        signal: controller.signal,
      });
      if (controller.signal.aborted || field("url")?.value !== url) return;
      const values = {
        title: data.title,
        description: data.description,
        provider: data.suggested_provider,
      };
      let count = 0;
      for (const name of names) {
        const input = field(name);
        if (
          input &&
          empty.has(name) &&
          !touched.current.has(name) &&
          !input.value.trim() &&
          values[name]?.trim()
        ) {
          input.value = values[name]!;
          count++;
        }
      }
      if (count) {
        applied();
        setMessage("Details added. Review them before sharing.");
      } else {
        setMessage(
          Object.values(values).some((value) => value?.trim())
            ? "Your existing fields were preserved. No details were added."
            : "No usable details were found. You can enter them yourself.",
        );
      }
    } catch {
      if (!controller.signal.aborted)
        setError("We couldn’t fetch details. You can enter them yourself.");
    } finally {
      if (request.current === controller) {
        request.current = null;
        setPending(false);
      }
    }
  }
  return { pending, message, error, changed, cancel, fetchDetails };
}
