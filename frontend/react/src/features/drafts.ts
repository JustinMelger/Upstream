import { useEffect, useRef, useState, type RefObject } from "react";
export type DraftItem = { type: string; id: number; title: string };
type Draft = { version: 1; values: Record<string, string>; items: DraftItem[] };
const prefix = "learning:draft:v1:";
const ownerKey = "learning:draft-owner";
let generation = 0;
export function clearDrafts() {
  generation++;
  try {
    for (const key of Object.keys(sessionStorage))
      if (key.startsWith(prefix)) sessionStorage.removeItem(key);
    sessionStorage.removeItem(ownerKey);
  } catch {
    /* Forms report unavailable storage; authentication must remain usable. */
  }
}
export function claimDrafts(username: string) {
  try {
    const owner = sessionStorage.getItem(ownerKey);
    if (owner && owner !== username) clearDrafts();
    sessionStorage.setItem(ownerKey, username);
  } catch {
    /* See clearDrafts. */
  }
}
const fields = new Set([
  "url",
  "title",
  "name",
  "description",
  "learning_outcomes",
  "prerequisites",
  "language",
  "provider",
  "category",
  "level",
  "duration_hours",
  "tags",
  "recommendation_note",
]);
function read(key: string): { draft: Draft | null; unavailable: boolean } {
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return { draft: null, unavailable: false };
    const draft = JSON.parse(raw);
    if (
      draft.version !== 1 ||
      !draft.values ||
      typeof draft.values !== "object" ||
      !Array.isArray(draft.items) ||
      !Object.entries(draft.values).every(
        ([key, value]) => fields.has(key) && typeof value === "string",
      ) ||
      !draft.items.every(
        (item: DraftItem) =>
          item &&
          ["course", "article", "video"].includes(item.type) &&
          Number.isSafeInteger(item.id) &&
          typeof item.title === "string",
      )
    ) {
      sessionStorage.removeItem(key);
      return { draft: null, unavailable: false };
    }
    return { draft, unavailable: false };
  } catch {
    return { draft: null, unavailable: true };
  }
}
export function useDraft(
  username: string,
  identity: string,
  form: RefObject<HTMLFormElement | null>,
  items: DraftItem[],
) {
  const key = prefix + encodeURIComponent(username) + ":" + identity;
  const [initial] = useState(() => read(key));
  const [saveState, setSaveState] = useState<"idle" | "pending" | "saved">(
    "idle",
  );
  const [candidate, setCandidate] = useState(initial.draft),
    [unavailable, setUnavailable] = useState(initial.unavailable);
  const itemsRef = useRef(items);
  itemsRef.current = items;
  const valuesRef = useRef<Record<string, string>>({});
  const dirty = useRef(false),
    finished = useRef(false),
    epoch = useRef(generation);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const saveRef = useRef(() => {});
  saveRef.current = () => {
    if (!dirty.current || finished.current || generation !== epoch.current)
      return;
    const values = valuesRef.current;
    try {
      sessionStorage.setItem(
        key,
        JSON.stringify({ version: 1, values, items: itemsRef.current }),
      );
      dirty.current = false;
      setSaveState("saved");
    } catch {
      setUnavailable(true);
    }
  };
  function changed() {
    if (form.current)
      valuesRef.current = Object.fromEntries(
        Array.from(form.current.elements)
          .filter(
            (
              field,
            ): field is
              HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement =>
              (field instanceof HTMLInputElement ||
                field instanceof HTMLTextAreaElement ||
                field instanceof HTMLSelectElement) &&
              fields.has(field.name),
          )
          .map((field) => [field.name, field.value]),
      );
    dirty.current = true;
    setSaveState("pending");
    clearTimeout(timer.current);
    timer.current = setTimeout(() => saveRef.current(), 500);
  }
  // Item moves/additions commit React state before the scheduled serialization.
  useEffect(() => {
    if (dirty.current) {
      clearTimeout(timer.current);
      timer.current = setTimeout(() => saveRef.current(), 500);
    }
  }, [items]);
  useEffect(() => {
    const flush = () => {
      clearTimeout(timer.current);
      saveRef.current();
    };
    window.addEventListener("pagehide", flush);
    return () => {
      flush();
      window.removeEventListener("pagehide", flush);
    };
  }, []);
  function discard() {
    clearTimeout(timer.current);
    dirty.current = false;
    setCandidate(null);
    setSaveState("idle");
    try {
      sessionStorage.removeItem(key);
    } catch {
      setUnavailable(true);
    }
  }
  function complete() {
    finished.current = true;
    discard();
  }
  function restore() {
    if (!candidate || !form.current) return null;
    for (const [name, value] of Object.entries(candidate.values)) {
      const field = form.current.elements.namedItem(name);
      if (
        field instanceof HTMLInputElement ||
        field instanceof HTMLTextAreaElement ||
        field instanceof HTMLSelectElement
      )
        field.value = value;
    }
    setCandidate(null);
    changed();
    return candidate;
  }
  return {
    candidate,
    unavailable,
    saveState,
    changed,
    discard,
    complete,
    restore,
  };
}
