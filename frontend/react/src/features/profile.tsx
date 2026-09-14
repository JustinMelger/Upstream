import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Plus } from "lucide-react";
import { Link } from "react-router";

import { ResourceArtwork, ResourceCard } from "../components/resources";
import { Empty, ErrorPanel, Loading } from "../components/ui";
import uiStyles from "../components/ui.module.css";
import {
  api,
  type LearningItem,
  type Page,
  type Summary,
} from "../lib/api/client";
import { useAuth } from "./auth";
import s from "./pages.module.css";
import pageStyles from "./profile.module.css";
import d from "./supporting.module.css";

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
      <header className={pageStyles.profileIdentity}>
        <span className={pageStyles.avatar} aria-hidden="true">
          {user?.username.slice(0, 2).toUpperCase()}
        </span>
        <div>
          <div className={pageStyles.identityLine}>
            <h1>{user?.username}</h1>
            <span className={s.badge}>
              {user?.role === "admin" ? "Administrator" : "Member"}
            </span>
          </div>
        </div>
        <div className={pageStyles.profileArtwork}>
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
        <nav
          className={pageStyles.profileTotals}
          aria-label="Your learning totals"
        >
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
          </div>
          <div className={uiStyles.actions}>
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
