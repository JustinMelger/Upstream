import { useState, type ReactNode } from "react";
import { Link, useLocation } from "react-router";
import {
  ArrowRight,
  BookOpen,
  FileText,
  Video,
  Route,
  Star,
} from "lucide-react";
import {
  detailUrl,
  type CatalogItem,
  type ContentType,
} from "../lib/api/client";
import s from "./resources.module.css";
import legacyArtwork from "./artwork-legacy.json";

export const contentIcons = {
  course: BookOpen,
  article: FileText,
  video: Video,
  path: Route,
};
/** Selects a stable technical illustration from each format's ten-cover library. */
export function artworkKey(type: ContentType, title: string) {
  const normalized = `${type}:${title.normalize("NFKC").trim().toLowerCase().replace(/\s+/g, " ")}`;
  let hash = 2166136261;
  for (const character of normalized)
    hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
  const fingerprint = String(hash >>> 0);
  const preserved = (legacyArtwork as Record<string, number>)[fingerprint];
  return `${type}-${preserved ?? (hash >>> 0) % 10}`;
}
export function ResourceArtwork({
  type,
  title,
  eager = false,
  hero = false,
}: {
  type: ContentType;
  title: string;
  eager?: boolean;
  hero?: boolean;
}) {
  const key = artworkKey(type, title);
  const resourceKey = `${key}:${title}`;
  const [failed, setFailed] = useState("");
  const Icon = contentIcons[type];
  return (
    <div
      className={s.artwork}
      data-content-type={type}
      data-artwork={key}
      data-hero={hero}
      aria-hidden="true"
    >
      {failed === resourceKey ? (
        <div className={s.fallback}>
          <Icon size={32} />
          <strong>{title}</strong>
          <span>{type}</span>
        </div>
      ) : (
        <img
          src={`/artwork/${key}-card.webp?v=refined-1`}
          srcSet={`/artwork/${key}-card.webp?v=refined-1 640w, /artwork/${key}.webp?v=refined-1 1280w`}
          sizes={
            hero
              ? "(max-width: 599px) 100px, 50vw"
              : "(max-width: 599px) 100vw, (max-width: 899px) 50vw, 33vw"
          }
          width={1280}
          height={720}
          alt=""
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          onError={() => setFailed(resourceKey)}
        />
      )}
    </div>
  );
}
export function ContentLabel({ type }: { type: ContentType }) {
  const Icon = contentIcons[type];
  return (
    <span className={s.type} data-content-type={type}>
      <Icon size={15} />
      {type}
    </span>
  );
}
export function Contributor({
  username,
  prefix = "Shared by",
}: {
  username?: string | null;
  prefix?: string;
}) {
  return (
    <span className={s.contributor}>
      <span className={s.initials} aria-hidden="true">
        {(username || "LH").slice(0, 2).toUpperCase()}
      </span>
      <span>
        {username ? `${prefix} ${username}`.trim() : "Shared learning"}
      </span>
    </span>
  );
}
export function Rating({ rating, count }: { rating: number; count: number }) {
  return count > 0 ? (
    <span className={s.rating}>
      <Star size={15} />
      {rating.toFixed(1)} · {count} {count === 1 ? "review" : "reviews"}
    </span>
  ) : null;
}
export type ResourcePreview = Pick<CatalogItem, "type" | "title"> &
  Partial<CatalogItem>;
export function ResourceInfo({
  item,
  compact = false,
}: {
  item: ResourcePreview;
  compact?: boolean;
}) {
  const note = item.recommendation_note?.trim(),
    description = item.description?.trim();
  return (
    <div className={s.info}>
      {!compact && description && (
        <p className={s.description}>{description}</p>
      )}
      {!compact && note && note !== description && (
        <blockquote className={s.quote}>“{note}”</blockquote>
      )}
      <div className={s.metadata}>
        {item.provider && <span>{item.provider}</span>}
        {item.level && <span>{item.level}</span>}
        {item.duration_hours != null && <span>{item.duration_hours}h</span>}
      </div>
      <footer>
        <Contributor username={item.created_by} />
        <Rating rating={item.rating || 0} count={item.review_count || 0} />
      </footer>
    </div>
  );
}
export function ResourceCard({
  item,
  compact = false,
  children,
  preview = false,
}: {
  item: ResourcePreview;
  compact?: boolean;
  children?: ReactNode;
  preview?: boolean;
}) {
  const location = useLocation();
  const context =
    location.pathname === "/explore"
      ? { catalogReturn: location.pathname + location.search }
      : undefined;
  const identity = (
    <>
      <ResourceArtwork type={item.type} title={item.title} />
      <div className={s.identity}>
        <ContentLabel type={item.type} />
        <h3>{item.title}</h3>
      </div>
    </>
  );
  return (
    <article
      className={`${s.card} ${compact ? s.compact : ""}`}
      data-content-type={item.type}
      data-resource-id={item.id == null ? undefined : `${item.type}:${item.id}`}
    >
      {preview ? (
        <div>{identity}</div>
      ) : (
        <Link
          className={s.identityLink}
          aria-label={item.title}
          to={detailUrl(item.type, item.id!)}
          state={context}
        >
          {identity}
        </Link>
      )}
      <ResourceInfo item={item} compact={compact} />
      {children}
    </article>
  );
}
export function Spotlight({ item }: { item: CatalogItem }) {
  const location = useLocation();
  return (
    <section
      className={s.spotlight}
      data-content-type={item.type}
      aria-label="Recently shared spotlight"
      data-resource-id={`${item.type}:${item.id}`}
    >
      <Link
        className={s.spotlightLink}
        aria-label={item.title}
        to={detailUrl(item.type, item.id)}
        state={{ catalogReturn: location.pathname + location.search }}
      >
        <div className={s.spotlightCopy}>
          <span className={s.type}>Recently shared · {item.type}</span>
          <h2>{item.title}</h2>
          <p>
            {item.recommendation_note
              ? `“${item.recommendation_note}”`
              : item.description}
          </p>
          <Contributor username={item.created_by} />
          <Rating rating={item.rating} count={item.review_count} />
          <span className={s.view}>
            View {item.type}
            <ArrowRight size={16} />
          </span>
        </div>
        <ResourceArtwork type={item.type} title={item.title} hero eager />
      </Link>
    </section>
  );
}
