import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";

import {
  ContentLabel,
  Contributor,
  ResourceArtwork,
} from "../components/resources";
import {
  Empty,
  ErrorPanel,
  Heading,
  Loading,
  Pagination,
  Stats,
} from "../components/ui";
import {
  type ActivityEvent,
  api,
  detailUrl,
  type Page,
  queryString,
  type Summary,
} from "../lib/api/client";
import pageStyles from "./activity.module.css";
import { useFilters } from "./filters";
import s from "./pages.module.css";
import d from "./supporting.module.css";

export function ActivityPage() {
  const { params, page, updateMany, update } = useFilters();
  const stats = params.get("view") === "stats";
  const scope = params.get("scope") || "personal";
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
      <Heading title="Activity" />
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
                className={pageStyles.statRow}
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
          <div className={pageStyles.feed}>
            {query.data.items.map((event) => {
              const target =
                detailUrl(event.type, event.content_id) +
                (event.event_type === "review" ? "?view=reviews#reviews" : "");

              return (
                <article
                  className={pageStyles.event}
                  key={event.event_id}
                  data-content-type={event.type}
                >
                  <Link
                    className={pageStyles.eventLink}
                    to={target}
                    aria-label={
                      event.event_type === "review"
                        ? `Read review of ${event.title}`
                        : event.title
                    }
                  >
                    <div className={pageStyles.eventArtwork}>
                      <ResourceArtwork type={event.type} title={event.title} />
                    </div>
                    <h2>{event.title}</h2>
                  </Link>
                  <div className={pageStyles.eventMeta}>
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
                  <div className={pageStyles.eventBody}>
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
