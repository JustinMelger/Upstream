import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { DropdownMenu } from "radix-ui";
import { useState } from "react";
import { Link } from "react-router";

import { ResourceArtwork, ResourceCard } from "../components/resources";
import {
  Empty,
  ErrorPanel,
  Heading,
  Loading,
  Pagination,
} from "../components/ui";
import {
  api,
  detailUrl,
  externalUrl,
  humanError,
  type LearningItem,
  type Page,
  queryString,
  send,
  type Summary,
} from "../lib/api/client";
import { useAuth } from "./auth";
import { CourseActions, useCourseJourney } from "./course-journey";
import { useFilters } from "./filters";
import pageStyles from "./learning.module.css";
import s from "./pages.module.css";

function LearningRow({ item }: { item: LearningItem }) {
  const cache = useQueryClient();
  const [saved, setSaved] = useState(false);
  const mutation = useMutation({
    mutationFn: (status: string) =>
      send(`/paths/${item.id}/status`, { status }),
    onSuccess: async () => {
      setSaved(true);
      await cache.invalidateQueries();
    },
  });

  function change(status: string) {
    setSaved(false);
    mutation.mutate(status);
  }

  if (item.type === "course")
    return (
      <ResourceCard item={item} compact>
        {item.status && (
          <div className={pageStyles.collectionActions}>
            <CourseActions course={item} />
          </div>
        )}
      </ResourceCard>
    );

  return (
    <ResourceCard item={item} compact>
      {item.status && (
        <div className={pageStyles.collectionActions}>
          <div className={pageStyles.actions}>
            <DropdownMenu.Root>
              <DropdownMenu.Trigger
                className="secondary"
                disabled={mutation.isPending}
                aria-busy={mutation.isPending}
                aria-label={`${item.title}: path status`}
              >
                {item.status.replaceAll("_", " ")} ▾
              </DropdownMenu.Trigger>
              <DropdownMenu.Portal>
                <DropdownMenu.Content className={s.menu} sideOffset={6}>
                  <DropdownMenu.RadioGroup
                    value={item.status}
                    onValueChange={change}
                  >
                    {["interested", "in_progress", "completed"].map(
                      (status) => (
                        <DropdownMenu.RadioItem key={status} value={status}>
                          {status.replaceAll("_", " ")}
                        </DropdownMenu.RadioItem>
                      ),
                    )}
                  </DropdownMenu.RadioGroup>
                </DropdownMenu.Content>
              </DropdownMenu.Portal>
            </DropdownMenu.Root>
          </div>
          {item.course_progress && item.course_progress.total > 0 && (
            <div className={pageStyles.pathProgress}>
              <p>
                {item.course_progress.completed} of {item.course_progress.total}{" "}
                courses completed
              </p>
              <progress
                aria-label={`${item.title}: courses completed`}
                value={item.course_progress.completed}
                max={item.course_progress.total}
              />
            </div>
          )}
          {item.type === "path" && (
            <small className="muted">Path status is set independently.</small>
          )}
          {mutation.error && (
            <p role="alert" className={s.error}>
              {humanError(mutation.error)} Your previous status is unchanged.
              Try again.
            </p>
          )}
          {saved && <small role="status">Progress saved.</small>}
        </div>
      )}
    </ResourceCard>
  );
}

export function Learning() {
  const journey = useCourseJourney();
  const { user } = useAuth();
  const { params, page, update } = useFilters();
  const view =
    params.get("view") ||
    (params.get("tab") === "shared" ? "contributions" : "tracked");
  const status = params.get("status") || "in_progress";
  const summary = useQuery({
    queryKey: ["learning-summary"],
    queryFn: () => api<Summary>("/learning/summary"),
  });
  const query = useQuery({
    queryKey: ["learning", view, status, page],
    queryFn: () =>
      api<Page<LearningItem>>(
        "/learning/items?" +
          queryString({
            view,
            status: view === "tracked" ? status : null,
            page,
          }),
      ),
  });
  const showPathPreview =
    view === "tracked" && status === "in_progress" && page === 1;
  const pathPreview = useQuery({
    queryKey: ["learning-path-preview"],
    queryFn: () =>
      api<Page<LearningItem>>("/learning/items?view=paths&page_size=1"),
    enabled: showPathPreview,
  });
  const next = summary.data?.next_course;
  const nextUrl = externalUrl(next?.url);

  return (
    <>
      <Heading
        eyebrow={`Good to see you, ${user?.username || "learner"}.`}
        title="My learning"
      />
      {summary.isPending ? (
        <Loading />
      ) : summary.error ? (
        <ErrorPanel
          error={summary.error}
          retry={() => void summary.refetch()}
        />
      ) : (
        <section
          className={pageStyles.continuePanel}
          aria-label="Continue learning"
        >
          {next && (
            <ResourceArtwork type="course" title={next.title} hero eager />
          )}
          <div className={pageStyles.continueCopy}>
            <span className="muted">
              {next
                ? next.status === "in_progress"
                  ? "Pick up where you left off"
                  : "Your next step"
                : "Your next discovery starts here"}
            </span>
            <h2>{next?.title || "Find something you want to learn."}</h2>
            {next && (
              <p className="muted">
                {[
                  next.provider,
                  next.duration_hours != null
                    ? `${next.duration_hours} hours`
                    : null,
                  next.status?.replaceAll("_", " "),
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            )}
            <div className={pageStyles.actions}>
              {next ? (
                <CourseActions
                  course={next}
                  suggestion
                  statusControls={false}
                />
              ) : (
                <Link className="button" to="/explore">
                  Explore learning <ArrowRight size={16} />
                </Link>
              )}
              {nextUrl && next && (
                <Link
                  className={s.textAction}
                  to={detailUrl("course", next.id)}
                >
                  View details
                </Link>
              )}
            </div>
          </div>
        </section>
      )}
      <div className={pageStyles.learningNav}>
        <div className={pageStyles.tabs}>
          {[
            ["tracked", "Courses"],
            ["paths", "Selected paths"],
          ].map(([key, label]) => (
            <button
              key={key}
              className={view === key ? pageStyles.active : ""}
              aria-pressed={view === key}
              onClick={() => update("view", key)}
            >
              {label}
              {key === "paths" && summary.data
                ? ` (${summary.data.selected_paths})`
                : ""}
            </button>
          ))}
        </div>
        <Link
          to="/home?view=contributions"
          aria-current={view === "contributions" ? "page" : undefined}
        >
          My contributions
        </Link>
      </div>
      {view === "tracked" && (
        <nav className={pageStyles.statusTabs} aria-label="Course status">
          {[
            ["in_progress", "In progress"],
            ["interested", "Interested"],
            ["completed", "Completed"],
          ].map(([key, label]) => (
            <Link
              key={key}
              to={`/home?view=tracked&status=${key}`}
              className={status === key ? pageStyles.active : ""}
              aria-current={status === key ? "page" : undefined}
            >
              {label}{" "}
              <span>
                {summary.data?.[
                  key as "interested" | "in_progress" | "completed"
                ] ?? "—"}
              </span>
            </Link>
          ))}
        </nav>
      )}
      {view === "contributions" && <h2>My contributions</h2>}
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorPanel error={query.error} retry={() => void query.refetch()} />
      ) : (
        <>
          {query.data.items.length ? (
            <div className={s.collectionGrid}>
              {query.data.items.map((item) => (
                <LearningRow key={`${item.type}:${item.id}`} item={item} />
              ))}
            </div>
          ) : view === "tracked" ? (
            <Empty
              title={
                status === "interested"
                  ? "Nothing on your learning list yet."
                  : status === "completed"
                    ? "Your completed courses will appear here."
                    : journey.notice?.completed &&
                        journey.notice.previous === "in_progress" &&
                        summary.data?.in_progress === 0
                      ? "You’ve finished your in-progress courses."
                      : "No courses in progress."
              }
              action={!(status === "in_progress" && !!summary.data?.interested)}
            >
              {status === "in_progress" && !!summary.data?.interested ? (
                <Link to="/home?view=tracked&status=interested">
                  View interested courses
                </Link>
              ) : (
                "Find a course that catches your curiosity."
              )}
            </Empty>
          ) : (
            <Empty
              title={
                view === "contributions"
                  ? "Your next find could help someone."
                  : "A fresh start awaits."
              }
            >
              {view === "contributions"
                ? "Share a resource and tell people why it matters."
                : "Find a course or path that catches your curiosity."}
            </Empty>
          )}
          <Pagination
            page={page}
            total={query.data.total}
            onChange={(p) => update("page", String(p))}
          />
        </>
      )}
      {showPathPreview &&
        (pathPreview.error ? (
          <ErrorPanel
            error={pathPreview.error}
            retry={() => void pathPreview.refetch()}
          />
        ) : (
          pathPreview.data?.items[0] && (
            <section className={pageStyles.pathPreview}>
              <h2>Your selected path</h2>
              <LearningRow item={pathPreview.data.items[0]} />
            </section>
          )
        ))}
    </>
  );
}
