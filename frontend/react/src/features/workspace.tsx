import {
  ResourceCard,
  ResourceArtwork,
  Contributor,
  ContentLabel,
} from "../components/resources";
import { DropdownMenu } from "radix-ui";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router";
import { ArrowRight, Plus } from "lucide-react";
import {
  api,
  send,
  humanError,
  queryString,
  detailUrl,
  externalUrl,
  type Page,
  type LearningItem,
  type Summary,
  type ActivityEvent,
} from "../lib/api/client";
import {
  Empty,
  ErrorPanel,
  Heading,
  Loading,
  Pagination,
  Stats,
} from "../components/ui";
import { useAuth } from "./auth";
import { useFilters } from "./filters";
import s from "./pages.module.css";
import { CourseActions, useCourseJourney } from "./course-journey";
import d from "./supporting.module.css";
export { Explore } from "./explore";
export function LearningRow({ item }: { item: LearningItem }) {
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
          <div className={s.collectionActions}>
            <CourseActions course={item} />
          </div>
        )}
      </ResourceCard>
    );
  return (
    <ResourceCard item={item} compact>
      {item.status && (
        <div className={s.collectionActions}>
          <div className={s.actions}>
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
            <div className={s.pathProgress}>
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
      (params.get("tab") === "shared" ? "contributions" : "tracked"),
    status = params.get("status") || "in_progress";
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
        <section className={s.continuePanel} aria-label="Continue learning">
          {next && (
            <ResourceArtwork type="course" title={next.title} hero eager />
          )}
          <div className={s.continueCopy}>
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
            <div className={s.actions}>
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
      <div className={s.learningNav}>
        <div className={s.tabs}>
          {[
            ["tracked", "Courses"],
            ["paths", "Selected paths"],
          ].map(([key, label]) => (
            <button
              key={key}
              className={view === key ? s.active : ""}
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
        <nav className={s.statusTabs} aria-label="Course status">
          {[
            ["in_progress", "In progress"],
            ["interested", "Interested"],
            ["completed", "Completed"],
          ].map(([key, label]) => (
            <Link
              key={key}
              to={`/home?view=tracked&status=${key}`}
              className={status === key ? s.active : ""}
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
            <section className={s.pathPreview}>
              <h2>Your selected path</h2>
              <LearningRow item={pathPreview.data.items[0]} />
            </section>
          )
        ))}
    </>
  );
}
export function ActivityPage() {
  const { params, page, updateMany, update } = useFilters();
  const stats = params.get("view") === "stats",
    scope = params.get("scope") || "personal";
  const summary = useQuery({
    queryKey: ["learning-summary"],
    queryFn: () => api<Summary>("/learning/summary"),
    enabled: stats,
  });
  const query = useQuery({
    queryKey: ["activity", scope, page],
    queryFn: () =>
      api<Page<ActivityEvent>>("/activity?" + queryString({ scope, page })),
    enabled: !stats,
  });
  return (
    <>
      <Heading title="Activity">
        See what people are sharing and how your learning is growing.
      </Heading>
      {params.get("retired") === "teams" && (
        <p className={s.notice} role="status">
          Teams has been retired. Shared learning and personal updates now live
          here.
        </p>
      )}
      <div className={s.tabs} aria-label="Activity views">
        {[
          ["personal", "For you"],
          ["shared", "Shared activity"],
          ["stats", "My stats"],
        ].map(([key, label]) => (
          <button
            key={key}
            className={(stats ? "stats" : scope) === key ? s.active : ""}
            aria-pressed={(stats ? "stats" : scope) === key}
            onClick={() =>
              updateMany({
                view: key === "stats" ? "stats" : "",
                scope: key === "stats" ? "" : key,
              })
            }
          >
            {label}
          </button>
        ))}
      </div>
      {stats ? (
        summary.isPending ? (
          <Loading />
        ) : summary.error ? (
          <ErrorPanel
            error={summary.error}
            retry={() => void summary.refetch()}
          />
        ) : (
          <>
            <h2>Your learning, at a glance</h2>
            <Stats summary={summary.data} />
            <section className={s.panel}>
              <Link
                className={s.statRow}
                to="/home?view=tracked&status=interested"
              >
                Courses you’re interested in
                <strong>{summary.data.interested}</strong>
              </Link>
              <p className="muted">
                Your current totals. Every step is yours to take.
              </p>
            </section>
          </>
        )
      ) : query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorPanel error={query.error} retry={() => void query.refetch()} />
      ) : query.data.items.length ? (
        <>
          <div className={d.feed}>
            {query.data.items.map((event) => {
              const target =
                detailUrl(event.type, event.content_id) +
                (event.event_type === "review" ? "?view=reviews#reviews" : "");
              return (
                <article
                  className={d.event}
                  key={event.event_id}
                  data-content-type={event.type}
                >
                  <Link
                    className={d.eventLink}
                    to={target}
                    aria-label={
                      event.event_type === "review"
                        ? `Read review of ${event.title}`
                        : event.title
                    }
                  >
                    <div className={d.eventArtwork}>
                      <ResourceArtwork type={event.type} title={event.title} />
                    </div>
                    <h2>{event.title}</h2>
                  </Link>
                  <div className={d.eventMeta}>
                    <Contributor username={event.actor} prefix="" />
                    <span>
                      {event.event_type === "share" ? "shared" : "reviewed"}
                    </span>
                    <ContentLabel type={event.type} />
                    <time className={d.timestamp} dateTime={event.happened_at}>
                      {new Date(event.happened_at).toLocaleString(undefined, {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </time>
                  </div>
                  <div className={d.eventBody}>
                    {event.rating != null && (
                      <span className={s.rating}>
                        ★ {event.rating} out of 5
                      </span>
                    )}
                    {event.excerpt &&
                      (event.excerpt_kind === "description" ? (
                        <p>{event.excerpt}</p>
                      ) : (
                        <blockquote>“{event.excerpt}”</blockquote>
                      ))}
                  </div>
                </article>
              );
            })}
          </div>
          <Pagination
            page={page}
            total={query.data.total}
            onChange={(p) => update("page", String(p))}
          />
        </>
      ) : (
        <Empty title="You’re all caught up.">
          {scope === "personal"
            ? "Reviews on your shared learning will appear here."
            : "New shares and reviews will appear here as the library grows."}
        </Empty>
      )}
    </>
  );
}
export function Profile() {
  const { user } = useAuth();
  const summary = useQuery({
    queryKey: ["learning-summary"],
    queryFn: () => api<Summary>("/learning/summary"),
  });
  const contributions = useQuery({
    queryKey: ["learning-items", "contributions", "profile"],
    queryFn: () =>
      api<Page<LearningItem>>(
        "/learning/items?view=contributions&page=1&page_size=3",
      ),
  });
  return (
    <>
      <header className={d.profileIdentity}>
        <span className={d.avatar} aria-hidden="true">
          {user?.username.slice(0, 2).toUpperCase()}
        </span>
        <div>
          <div className={d.identityLine}>
            <h1>{user?.username}</h1>
            <span className={s.badge}>
              {user?.role === "admin" ? "Administrator" : "Member"}
            </span>
          </div>
          <p className="muted">Your learning, and the ideas you’ve shared.</p>
        </div>
        <div className={d.profileArtwork}>
          <ResourceArtwork type="course" title="Your learning library" eager />
        </div>
      </header>
      {summary.isPending ? (
        <Loading />
      ) : summary.error ? (
        <ErrorPanel
          error={summary.error}
          retry={() => void summary.refetch()}
        />
      ) : (
        <nav className={d.profileTotals} aria-label="Your learning totals">
          <Link to="/home?view=tracked&status=in_progress">
            <strong>{summary.data.in_progress}</strong>
            <span>In progress →</span>
          </Link>
          <Link to="/home?view=tracked&status=completed">
            <strong>{summary.data.completed}</strong>
            <span>Completed →</span>
          </Link>
          <Link to="/home?view=paths">
            <strong>{summary.data.selected_paths}</strong>
            <span>Selected paths →</span>
          </Link>
          <Link to="/activity?view=stats">
            View my stats <ArrowRight size={16} />
          </Link>
        </nav>
      )}
      <section className={d.section}>
        <div className={d.sectionHeading}>
          <div>
            <h2>Your contributions</h2>
            <p className="muted">
              Resources you’ve shared with the Learning Hub community.
            </p>
          </div>
          <div className={s.actions}>
            <Link className="button" to="/share/item">
              <Plus size={16} />
              Share something
            </Link>
            <Link className={s.textAction} to="/home?view=contributions">
              View all contributions <ArrowRight size={16} />
            </Link>
          </div>
        </div>
        {contributions.isPending ? (
          <Loading />
        ) : contributions.error ? (
          <ErrorPanel
            error={contributions.error}
            retry={() => void contributions.refetch()}
          />
        ) : contributions.data.items.length ? (
          <div className={s.collectionGrid}>
            {contributions.data.items.map((item) => (
              <ResourceCard key={`${item.type}:${item.id}`} item={item} />
            ))}
          </div>
        ) : (
          <Empty title="Your library starts with one good find." action={false}>
            Share a resource that helped you learn. It will appear here for you
            to revisit.
          </Empty>
        )}
      </section>
    </>
  );
}
