import type { components } from "./generated";
export type Session = components["schemas"]["BrowserSession"];
export type LearningItem = components["schemas"]["LearningItem"];
export type CatalogItem = components["schemas"]["CatalogItem"];
export type ContentType = CatalogItem["type"];
export type Summary = components["schemas"]["LearningSummary"];
export type ActivityEvent = components["schemas"]["ActivityEvent"];
export type PathProgress = components["schemas"]["PathProgress"];
export type Review = {
  id: number;
  rating: number;
  text?: string | null;
  created_by: string;
  created_at: string;
};
export type Content = Omit<
  Partial<components["schemas"]["CoursePayload"]>,
  "description"
> & {
  description?: string | null;
  id: number;
  name?: string;
  title?: string;
  tags?: string | null;
  recommendation_note?: string | null;
  items?: { type: string; id: number; title: string; url?: string }[];
};
export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
let csrf = "";
export function setCsrf(value: string) {
  csrf = value;
}
export function safeReturn(value: string | null): string {
  return value?.startsWith("/") &&
    !value.startsWith("//") &&
    !/[\\\r\n]/.test(value) &&
    !value.startsWith("/login")
    ? value
    : "/home";
}
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch("/api" + path, {
    ...init,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(csrf ? { "X-CSRF-Token": csrf } : {}),
      ...init.headers,
    },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401)
      window.dispatchEvent(new Event("session-expired"));
    throw new ApiError(
      response.status,
      body?.message || body?.detail || "The request could not be completed.",
    );
  }
  return normalizeIds(body) as T;
}
// Legacy mutation responses serialize numeric content IDs as strings.
// Keep usernames and stable event identifiers untouched.
function normalizeIds(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(normalizeIds);
  if (value && typeof value === "object")
    return Object.fromEntries(
      Object.entries(value).map(([key, child]) => [
        key,
        /^(id|course_id|article_id|video_id|path_id|content_id|review_id)$/.test(
          key,
        ) &&
        typeof child === "string" &&
        /^\d+$/.test(child) &&
        Number.isSafeInteger(Number(child))
          ? Number(child)
          : normalizeIds(child),
      ]),
    );
  return value;
}
export const send = <T>(path: string, body: unknown = {}, method = "POST") =>
  api<T>(path, { method, body: JSON.stringify(body) });
export function queryString(
  values: Record<string, string | number | null | undefined>,
) {
  return new URLSearchParams(
    Object.entries(values)
      .filter(([, v]) => v !== null && v !== undefined && v !== "")
      .map(([k, v]) => [k, String(v)]),
  ).toString();
}
export const plural = (type: ContentType) =>
  type === "path"
    ? "paths"
    : type === "article"
      ? "articles"
      : type === "video"
        ? "videos"
        : "courses";
export const detailUrl = (type: ContentType, id: number) =>
  `/explore/${plural(type)}/${id}`;
export const humanError = (error: unknown) =>
  error instanceof Error
    ? error.message.replaceAll("_", " ")
    : "Something went wrong. Please try again.";
export function externalUrl(value: string | undefined | null) {
  try {
    const url = new URL(value || "");
    return ["http:", "https:"].includes(url.protocol) ? url.href : undefined;
  } catch {
    return undefined;
  }
}
