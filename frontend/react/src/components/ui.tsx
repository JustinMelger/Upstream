import { ResourceCard } from "./resources";
import type { ReactNode } from "react";
import { Link } from "react-router";
import { Dialog } from "radix-ui";
import { BookOpen, X, RefreshCw } from "lucide-react";
import { humanError, type CatalogItem, type Summary } from "../lib/api/client";
import s from "../features/pages.module.css";
export function Loading() {
  return (
    <div className={s.loading} role="status" aria-label="Loading">
      <div />
      <div />
      <div />
      <span>Loading your workspace…</span>
    </div>
  );
}
export function ErrorPanel({
  error,
  retry,
}: {
  error: unknown;
  retry?: () => void;
}) {
  return (
    <div role="alert" className={s.empty}>
      <h2>We couldn’t load this.</h2>
      <p className="muted">{humanError(error)}</p>
      {retry && (
        <button type="button" onClick={retry}>
          <RefreshCw size={16} />
          Try again
        </button>
      )}
    </div>
  );
}
export function Empty({
  title,
  children,
  action = true,
}: {
  title: string;
  children: ReactNode;
  action?: boolean;
}) {
  return (
    <div className={s.empty}>
      <BookOpen size={28} />
      <h2>{title}</h2>
      <p className="muted">{children}</p>
      {action && (
        <Link className="button secondary" to="/explore">
          Explore the library
        </Link>
      )}
    </div>
  );
}
export function Heading({
  eyebrow,
  title,
  children,
  action,
}: {
  eyebrow?: string;
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <header className={s.heading}>
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {children && <p className="muted">{children}</p>}
      </div>
      {action}
    </header>
  );
}
export function ContentCard({
  item,
  row = false,
}: {
  item: CatalogItem;
  row?: boolean;
}) {
  return <ResourceCard item={item} compact={row} />;
}
export function Pagination({
  page,
  total,
  pageSize = 24,
  onChange,
}: {
  page: number;
  total: number;
  pageSize?: number;
  onChange: (page: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <nav aria-label="Pagination" className={s.pagination}>
      <span className="muted">
        {total} {total === 1 ? "result" : "results"}
        {pages > 1 && ` · Page ${page} of ${pages}`}
      </span>
      {pages > 1 && (
        <div>
          <button
            type="button"
            className="secondary"
            disabled={page <= 1}
            onClick={() => onChange(page - 1)}
          >
            Previous
          </button>
          <button
            type="button"
            className="secondary"
            disabled={page >= pages}
            onClick={() => onChange(page + 1)}
          >
            Next
          </button>
        </div>
      )}
    </nav>
  );
}
export function Stats({ summary }: { summary: Summary }) {
  return (
    <div className={s.stats}>
      {[
        [
          "In progress",
          summary.in_progress,
          "/home?view=tracked&status=in_progress",
        ],
        [
          "Courses completed",
          summary.completed,
          "/home?view=tracked&status=completed",
        ],
        ["Selected paths", summary.selected_paths, "/home?view=paths"],
        ["Contributions", summary.contributions, "/home?view=contributions"],
      ].map(([label, value, target]) => (
        <Link to={String(target)} key={label}>
          <span className="muted">{label}</span>
          <strong>{value}</strong>
          <small className="muted">View your learning</small>
        </Link>
      ))}
    </div>
  );
}
export function Confirm({
  title,
  description,
  onConfirm,
  busy,
  children,
}: {
  title: string;
  description: string;
  onConfirm: () => void;
  busy: boolean;
  children: ReactNode;
}) {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>{children}</Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className={s.overlay} />
        <Dialog.Content className={s.dialog}>
          <Dialog.Title>{title}</Dialog.Title>
          <Dialog.Description>{description}</Dialog.Description>
          <div className={s.actions}>
            <Dialog.Close asChild>
              <button className="secondary" disabled={busy}>
                Cancel
              </button>
            </Dialog.Close>
            <button
              className="danger"
              aria-busy={busy}
              disabled={busy}
              onClick={onConfirm}
            >
              {busy ? "Deleting…" : "Delete"}
            </button>
          </div>
          <Dialog.Close className={s.close} aria-label="Close">
            <X size={18} />
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
