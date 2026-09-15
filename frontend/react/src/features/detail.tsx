import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowUpRight, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router";

import {
  ContentLabel,
  Contributor,
  Rating,
  ResourceArtwork,
} from "../components/resources";
import { Confirm, Empty, ErrorPanel, Loading } from "../components/ui";
import {
  api,
  type CatalogItem,
  type Content,
  type ContentType,
  detailUrl,
  externalUrl,
  humanError,
  type Page,
  type PathProgress,
  type Review,
  send,
} from "../lib/api/client";
import { useAuth } from "./auth";
import { CourseActions } from "./course-journey";
import { Reviews } from "./details/Reviews";
import s from "./pages.module.css";
import d from "./supporting.module.css";

export function Detail() {
  const location = useLocation();
  const catalogReturn =
    typeof location.state?.catalogReturn === "string" &&
    /^\/explore(?:\?|$)/.test(location.state.catalogReturn)
      ? location.state.catalogReturn
      : "/explore";
  const { kind, id } = useParams();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const { user } = useAuth();
  const [params] = useSearchParams();
  const type = (
    {
      courses: "course",
      articles: "article",
      videos: "video",
      paths: "path",
    } as Record<string, ContentType>
  )[kind || ""];
  const contentId = Number(id);
  const valid = !!type && Number.isInteger(contentId) && contentId > 0;
  const base = `/${kind}/${contentId}`;
  const query = useQuery({
    queryKey: ["detail", type, contentId],
    queryFn: () => api<Content>(base),
    enabled: valid,
  });
  const reviews = useQuery({
    queryKey: ["reviews", type, contentId],
    queryFn: () => api<Review[]>(base + "/reviews"),
    enabled: valid,
  });
  const progress = useQuery({
    queryKey: ["progress", type, contentId],
    queryFn: () => api<PathProgress>(`/learning/paths/${contentId}`),
    enabled: valid && type === "path",
  });
  const tracked = useQuery({
    queryKey: ["tracking", contentId],
    queryFn: () =>
      api<Page<CatalogItem>>(
        `/learning/items?view=tracked&content_id=${contentId}`,
      ),
    enabled: valid && type === "course",
  });
  const [error, setError] = useState("");
  const mutate = useMutation({
    mutationFn: ({
      path,
      body = {},
      method = "POST",
    }: {
      path: string;
      body?: unknown;
      method?: string;
    }) => send(path, body, method),
    onSuccess: () => {
      setError("");
      void cache.invalidateQueries();
    },
    onError: (e) => setError(humanError(e)),
  });

  async function remove() {
    try {
      await mutate.mutateAsync({ path: base, method: "DELETE" });
      navigate("/explore");
    } catch {
      /* displayed above */
    }
  }

  if (!valid)
    return (
      <Empty title="This item isn’t here.">
        Return to Explore to find something useful.
      </Empty>
    );
  if (query.isPending) return <Loading />;
  if (query.error)
    return (
      <ErrorPanel error={query.error} retry={() => void query.refetch()} />
    );
  const content = query.data;
  const title = content.title || content.name || "Learning item";
  const owner = user?.role === "admin" || user?.username === content.created_by;
  const url = externalUrl(content.url);
  const description = content.description?.trim() || "";
  const summary =
    description.length > 240
      ? description.slice(0, 239).trimEnd() + "…"
      : description;
  const metadata = [
    content.provider,
    content.level,
    content.duration_hours != null ? `${content.duration_hours} hours` : null,
    content.language,
    content.category,
  ].filter(Boolean);

  return (
    <>
      <Link className={s.back} to={catalogReturn}>
        <ArrowLeft size={15} />
        Back to Explore
      </Link>
      {error && (
        <p role="alert" className={s.error}>
          {error}
        </p>
      )}
      <section className={d.intro} data-content-type={type}>
        <div className={d.introArtwork}>
          <ResourceArtwork type={type} title={title} hero eager />
        </div>
        <div className={d.introTitle}>
          <ContentLabel type={type} />
          <h1>{title}</h1>
        </div>
        {summary && <p className={d.summary}>{summary}</p>}
        <div className={d.primaryActions}>
          {url && type !== "course" && (
            <a
              className="button"
              href={url}
              target="_blank"
              rel="noopener noreferrer"
            >
              {
                {
                  course: "Open course",
                  article: "Read article",
                  video: "Watch video",
                  path: "Open resource",
                }[type]
              }
              <ArrowUpRight size={17} />
            </a>
          )}
          {type === "course" && (
            <CourseActions
              course={{
                id: contentId,
                title,
                url: content.url,
                status: tracked.data?.items[0]?.status,
              }}
              disabled={tracked.isPending || !!tracked.error}
            />
          )}
          {tracked.error && (
            <ErrorPanel
              error={tracked.error}
              retry={() => void tracked.refetch()}
            />
          )}
          {type === "path" && progress.data && (
            <>
              <button
                disabled={mutate.isPending}
                aria-busy={mutate.isPending}
                className={progress.data.selected ? "secondary" : ""}
                onClick={() =>
                  mutate.mutate({
                    path:
                      base + (progress.data.selected ? "/unselect" : "/select"),
                  })
                }
              >
                {progress.data.selected
                  ? "Remove from My learning"
                  : "Add to My learning"}
              </button>
              {progress.data.selected && (
                <label>
                  Path status
                  <select
                    disabled={mutate.isPending}
                    value={progress.data.status || "interested"}
                    onChange={(e) =>
                      mutate.mutate({
                        path: base + "/status",
                        body: { status: e.target.value },
                      })
                    }
                  >
                    <option value="interested">Interested</option>
                    <option value="in_progress">In progress</option>
                    <option value="completed">Completed</option>
                  </select>
                </label>
              )}
            </>
          )}
          {type === "path" && progress.isPending && (
            <span role="status">Loading your path…</span>
          )}
          {progress.error && (
            <ErrorPanel
              error={progress.error}
              retry={() => void progress.refetch()}
            />
          )}
        </div>
        <div className={d.metadata}>
          {metadata.length > 0 && <p>{metadata.join(" · ")}</p>}
          {type === "path" && (
            <p>
              {content.items?.length || 0}{" "}
              {content.items?.length === 1 ? "resource" : "resources"}
              {(["course", "article", "video"] as const).map((kind) => {
                const count =
                  content.items?.filter((item) => item.type === kind).length ||
                  0;

                return count
                  ? ` · ${count} ${kind}${count === 1 ? "" : "s"}`
                  : "";
              })}
            </p>
          )}
          <Contributor username={content.created_by} />
          {reviews.isPending ? (
            <span role="status">Loading reviews…</span>
          ) : reviews.error ? (
            <span className="muted">Rating unavailable</span>
          ) : reviews.data?.length ? (
            <Rating
              count={reviews.data.length}
              rating={
                reviews.data.reduce((sum, r) => sum + r.rating, 0) /
                reviews.data.length
              }
            />
          ) : (
            <span className="muted">No reviews yet</span>
          )}
        </div>
      </section>
      {owner && (
        <div className={d.ownerActions}>
          <Link
            className="button secondary"
            to={`/share/${type === "path" ? "path" : "item"}?type=${type}&edit=${contentId}`}
          >
            <Pencil size={15} />
            Edit
          </Link>
          <Confirm
            title={`Delete ${type}?`}
            description="This removes the content, its reviews, and references from learning paths. This cannot be undone."
            busy={mutate.isPending}
            onConfirm={() => void remove()}
          >
            <button className="secondary">
              <Trash2 size={15} />
              Delete
            </button>
          </Confirm>
        </div>
      )}
      {params.get("view") !== "reviews" && (
        <>
          {content.recommendation_note && (
            <section className={d.recommendation}>
              <Contributor
                username={content.created_by}
                prefix="Recommended by"
              />
              <blockquote>{content.recommendation_note}</blockquote>
            </section>
          )}
          {type === "path" && progress.data && (
            <section className={d.progress} aria-label="Your course progress">
              {progress.data.total > 0 ? (
                <>
                  <p>
                    {progress.data.completed} of {progress.data.total} courses
                    completed
                  </p>
                  <progress
                    aria-label="Courses completed"
                    value={progress.data.completed}
                    max={progress.data.total}
                  />
                </>
              ) : (
                <p>This path has no trackable courses.</p>
              )}
              <small className="muted">
                Course progress and path status are separate.
              </small>
            </section>
          )}
          {(description.length > 240 ||
            content.learning_outcomes ||
            content.prerequisites) && (
            <section className={d.section}>
              {description.length > 240 && (
                <>
                  <h2>About this {type}</h2>
                  <p className={s.prose}>{description}</p>
                </>
              )}
              {content.learning_outcomes && (
                <>
                  <h2>What you’ll learn</h2>
                  <p className={s.prose}>{content.learning_outcomes}</p>
                </>
              )}
              {content.prerequisites && (
                <>
                  <h2>Before you begin</h2>
                  <p className={s.prose}>{content.prerequisites}</p>
                </>
              )}
            </section>
          )}
          {type === "path" && (
            <section className={d.section}>
              <h2>Your path</h2>
              {content.items?.length ? (
                <ol className={d.pathList}>
                  {content.items.map((item, index) => {
                    const status = progress.data?.courses.find(
                      (c) => c.id === item.id,
                    )?.status;

                    return (
                      <li key={`${item.type}:${item.id}`}>
                        <Link
                          className={d.pathLink}
                          to={detailUrl(item.type as ContentType, item.id)}
                          state={{ catalogReturn }}
                        >
                          <span className={d.position}>{index + 1}</span>
                          <div className={d.thumbnail}>
                            <ResourceArtwork
                              type={item.type as ContentType}
                              title={item.title}
                            />
                          </div>
                          <div className={d.rowTitle}>
                            <ContentLabel type={item.type as ContentType} />
                            <strong>{item.title}</strong>
                          </div>
                          {item.type === "course" && (
                            <span className={s.badge} data-status={status}>
                              {progress.isPending
                                ? "Loading status…"
                                : progress.error
                                  ? "Status unavailable"
                                  : status
                                    ? status.replaceAll("_", " ")
                                    : "Not tracked"}
                            </span>
                          )}
                        </Link>
                      </li>
                    );
                  })}
                </ol>
              ) : (
                <Empty title="This path is empty." action={false}>
                  Items may have been removed. Its owner can add new learning
                  material.
                </Empty>
              )}
            </section>
          )}
        </>
      )}
      <Reviews
        reviews={reviews.data}
        loading={reviews.isPending}
        error={reviews.error}
        retry={() => void reviews.refetch()}
        base={base}
      />
    </>
  );
}
