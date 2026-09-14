import { useQueryClient } from "@tanstack/react-query";
import { ArrowUpRight, X } from "lucide-react";
import { DropdownMenu } from "radix-ui";
import {
  createContext,
  type ReactNode,
  useContext,
  useId,
  useRef,
  useState,
} from "react";
import { Link } from "react-router";

import { detailUrl, externalUrl, humanError, send } from "../lib/api/client";
import { useAuth } from "./auth";
import j from "./course-journey.module.css";
import s from "./pages.module.css";

export type CourseState = "interested" | "in_progress" | "completed" | null;

export type JourneyCourse = {
  id: number;
  title: string;
  url?: string | null;
  status?: string | null;
};

type Notice = {
  message: string;
  course?: JourneyCourse;
  completed?: boolean;
  previous?: CourseState;
  target?: string;
  targetLabel?: string;
  launchUrl?: string;
  undoing?: boolean;
  error?: string;
};

type ChangeOptions = {
  launch?: boolean;
  undo?: boolean;
  source?: string;
  focusOrigin?: HTMLElement | null;
};

type ActionError = { message: string; source?: string };

type JourneyContext = {
  notice: Notice | null;
  show: (notice: Notice) => void;
  dismiss: () => void;
  pending: Set<number>;
  errors: Record<number, ActionError>;
  change: (
    course: JourneyCourse,
    status: CourseState,
    options?: ChangeOptions,
  ) => Promise<void>;
  noticeRef: React.RefObject<HTMLElement | null>;
};

const Context = createContext<JourneyContext | null>(null);

/**
 * Share course mutations and feedback, resetting local state when the account changes.
 */
export function CourseJourneyProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();

  return (
    <JourneyState key={user?.username || "anonymous"}>{children}</JourneyState>
  );
}

function JourneyState({ children }: { children: ReactNode }) {
  const cache = useQueryClient();
  const [notice, show] = useState<Notice | null>(null);
  const [pending, setPending] = useState(new Set<number>());
  const pendingRef = useRef(new Set<number>());
  const [errors, setErrors] = useState<Record<number, ActionError>>({});
  const noticeRef = useRef<HTMLElement>(null);

  /**
   * Persist a course status before publishing success feedback or opening its URL.
   *
   * Ignore concurrent changes for the same course. Reserve a tab during the user
   * gesture when launching, close it on save failure, and offer a link if opening
   * fails. Refresh affected queries and move focus to feedback if the initiating
   * control disappears. A null status removes the course from My learning.
   */
  async function change(
    course: JourneyCourse,
    status: CourseState,
    options: ChangeOptions = {},
  ) {
    if (pendingRef.current.has(course.id)) return;
    const focused =
      options.focusOrigin ||
      (document.activeElement instanceof HTMLElement &&
      document.activeElement.closest("[data-resource-id]")
        ? document.activeElement
        : null);
    let tab: Window | null = null;
    const url = options.launch ? externalUrl(course.url) : undefined;

    if (url) {
      try {
        tab = window.open("about:blank", "_blank");

        if (tab) {
          tab.opener = null;
          tab.document.title = "Opening your course…";
          tab.document.body.textContent =
            "Saving your progress and opening your course…";
        }
      } catch {
        tab?.close();
        tab = null;
      }
    }

    pendingRef.current.add(course.id);
    setPending(new Set(pendingRef.current));
    setErrors((old) => ({ ...old, [course.id]: { message: "" } }));
    if (options.undo)
      show((old) => (old ? { ...old, undoing: true, error: undefined } : old));

    try {
      await send(
        status ? "/tracking" : "/tracking/delete",
        status ? { course_id: course.id, status } : { course_id: course.id },
      );
    } catch (error) {
      tab?.close();
      const message = `${humanError(error)} Your previous status is unchanged. Try again.`;
      setErrors((old) => ({
        ...old,
        [course.id]: { message, source: options.source },
      }));
      if (options.undo)
        show((old) => (old ? { ...old, undoing: false, error: message } : old));
      pendingRef.current.delete(course.id);
      setPending(new Set(pendingRef.current));

      return;
    }

    let launchUrl: string | undefined;

    if (url) {
      if (!tab || tab.closed) launchUrl = url;
      else {
        try {
          tab.location.replace(url);
        } catch {
          tab.close();
          launchUrl = url;
        }
      }
    }

    const completed = status === "completed" && !options.undo;
    show({
      message: options.undo
        ? "Completion undone. Your previous status is restored."
        : completed
          ? "Course completed. Nice work!"
          : status === null
            ? "Removed from My learning."
            : status === "interested" && !course.status
              ? "Added to My learning · Interested"
              : status === "in_progress"
                ? "Added to In progress."
                : "Progress saved.",
      course,
      completed,
      previous: (course.status as CourseState) || null,
      launchUrl,
      target: completed
        ? "/home?view=tracked&status=completed"
        : status
          ? `/home?view=tracked&status=${status}`
          : undefined,
      targetLabel: completed ? "View completed" : "View my learning",
    });

    try {
      await cache.invalidateQueries({
        predicate: (query) =>
          [
            "tracking",
            "progress",
            "learning",
            "learning-items",
            "learning-summary",
            "learning-path-preview",
          ].includes(String(query.queryKey[0])),
      });
    } finally {
      pendingRef.current.delete(course.id);
      setPending(new Set(pendingRef.current));
      requestAnimationFrame(() => {
        if (focused && !focused.isConnected) noticeRef.current?.focus();
      });
    }
  }

  return (
    <Context.Provider
      value={{
        notice,
        show,
        dismiss: () => show(null),
        pending,
        errors,
        change,
        noticeRef,
      }}
    >
      {children}
    </Context.Provider>
  );
}

/**
 * Access shared course actions and feedback.
 *
 * @throws When called outside CourseJourneyProvider.
 */
export function useCourseJourney() {
  const value = useContext(Context);
  if (!value) throw new Error("Course journey provider is required");

  return value;
}

/**
 * Bind shared course mutations to one rendered set of controls.
 *
 * Pending state is shared across copies of a course; errors appear only at the
 * control instance that initiated the failed request.
 */
export function useCourseActions(course: JourneyCourse) {
  const journey = useCourseJourney();
  const source = useId();

  return {
    pending: journey.pending.has(course.id),
    error:
      journey.errors[course.id]?.source === source
        ? journey.errors[course.id]?.message
        : undefined,
    change: (status: CourseState, options?: ChangeOptions) =>
      journey.change(course, status, { ...options, source }),
  };
}

/**
 * Render shared mutation feedback, including completion undo and blocked-tab recovery.
 */
export function CourseFeedback() {
  const { notice, dismiss, change, noticeRef, pending } = useCourseJourney();
  if (!notice) return null;
  const busy = notice.course ? pending.has(notice.course.id) : false;

  return (
    <section
      className={j.notice}
      ref={noticeRef}
      tabIndex={-1}
      aria-label="Learning update"
    >
      <p role="status" aria-live="polite">
        {notice.message}
      </p>
      {notice.course && (
        <span className={j.courseTitle}>{notice.course.title}</span>
      )}
      <div className={s.actions}>
        {notice.completed && notice.course && (
          <button
            className="secondary"
            disabled={busy}
            aria-busy={notice.undoing}
            onClick={() =>
              void change(
                { ...notice.course!, status: "completed" },
                notice.previous || null,
                { undo: true },
              )
            }
          >
            Undo
          </button>
        )}
        {notice.target && (
          <Link className={s.textAction} to={notice.target}>
            {notice.targetLabel}
          </Link>
        )}
        {notice.completed && notice.course && (
          <Link
            className={s.textAction}
            to={detailUrl("course", notice.course.id) + "?view=reviews#reviews"}
          >
            Review course
          </Link>
        )}
        {notice.launchUrl && (
          <a
            className="button"
            href={notice.launchUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            Open course <ArrowUpRight size={16} />
          </a>
        )}
      </div>
      {notice.launchUrl && (
        <p className="muted">
          Your progress is saved. Open the course when you’re ready.
        </p>
      )}
      {notice.error && (
        <p className={s.error} role="alert">
          {notice.error}
        </p>
      )}
      <button
        className={j.dismiss}
        aria-label="Dismiss learning update"
        disabled={notice.undoing}
        onClick={dismiss}
      >
        <X size={18} />
      </button>
    </section>
  );
}

export function CourseActions({
  course,
  disabled = false,
  statusControls = true,
  suggestion = false,
}: {
  course: JourneyCourse;
  disabled?: boolean;
  statusControls?: boolean;
  suggestion?: boolean;
}) {
  const action = useCourseActions(course);
  const controls = useRef<HTMLDivElement>(null);
  const url = externalUrl(course.url);
  const start =
    course.status === "interested" || (suggestion && !course.status);
  const busy = disabled || action.pending;

  return (
    <div className={j.controls} ref={controls}>
      <div className={s.actions}>
        {!url ? (
          <Link
            className="button secondary"
            to={detailUrl("course", course.id)}
          >
            View details
          </Link>
        ) : start ? (
          <button
            disabled={busy}
            aria-busy={action.pending}
            onClick={() => void action.change("in_progress", { launch: true })}
          >
            Start learning <ArrowUpRight size={16} />
          </button>
        ) : (
          <a
            className="button"
            href={url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {course.status === "in_progress"
              ? "Continue learning"
              : "Open course"}
            <ArrowUpRight size={16} />
          </a>
        )}
        {statusControls && (
          <>
            {!course.status ? (
              <button
                className="secondary"
                disabled={busy}
                aria-busy={action.pending}
                onClick={() => void action.change("interested")}
              >
                Add to My learning
              </button>
            ) : (
              <>
                {course.status === "in_progress" && (
                  <button
                    className="secondary"
                    disabled={busy}
                    aria-busy={action.pending}
                    onClick={() => void action.change("completed")}
                  >
                    Mark completed
                  </button>
                )}
                <DropdownMenu.Root>
                  <DropdownMenu.Trigger
                    className="secondary"
                    disabled={busy}
                    aria-label={`${course.title}: course progress`}
                  >
                    {course.status.replaceAll("_", " ")} ▾
                  </DropdownMenu.Trigger>
                  <DropdownMenu.Portal>
                    <DropdownMenu.Content className={s.menu} sideOffset={6}>
                      <DropdownMenu.RadioGroup
                        value={course.status}
                        onValueChange={(status) =>
                          void action.change(status as CourseState, {
                            focusOrigin: controls.current,
                          })
                        }
                      >
                        {["interested", "in_progress", "completed"].map(
                          (status) => (
                            <DropdownMenu.RadioItem key={status} value={status}>
                              {status.replaceAll("_", " ")}
                            </DropdownMenu.RadioItem>
                          ),
                        )}
                      </DropdownMenu.RadioGroup>
                      <DropdownMenu.Separator />
                      <DropdownMenu.Item
                        className={j.remove}
                        onSelect={() =>
                          void action.change(null, {
                            focusOrigin: controls.current,
                          })
                        }
                      >
                        Remove from My learning
                      </DropdownMenu.Item>
                    </DropdownMenu.Content>
                  </DropdownMenu.Portal>
                </DropdownMenu.Root>
              </>
            )}
          </>
        )}
      </div>
      {action.error && (
        <p className={s.error} role="alert">
          {action.error}
        </p>
      )}
    </div>
  );
}
