import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Star } from "lucide-react";
import { type FormEvent, useEffect, useRef } from "react";
import { useLocation } from "react-router";

import { Contributor } from "../../components/resources";
import { ErrorPanel, Loading } from "../../components/ui";
import { api, humanError, type Review, send } from "../../lib/api/client";
import { useAuth } from "../auth";
import s from "../pages.module.css";
import d from "../supporting.module.css";

export function Reviews({
  reviews,
  loading,
  error,
  retry,
  base,
}: {
  reviews?: Review[];
  loading: boolean;
  error: unknown;
  retry: () => void;
  base: string;
}) {
  const { user } = useAuth();
  const cache = useQueryClient();
  const reviewInput = useRef<HTMLTextAreaElement>(null);
  const location = useLocation();
  useEffect(() => {
    if (
      !loading &&
      (location.hash === "#reviews" ||
        new URLSearchParams(location.search).get("view") === "reviews")
    )
      document.getElementById("reviews")?.scrollIntoView();
  }, [loading, location.hash, location.search]);
  const mine = reviews?.find((r) => r.created_by === user?.username);
  const mutation = useMutation({
    mutationFn: ({ body, id }: { body?: unknown; id?: number }) =>
      id
        ? api(base + `/reviews/${id}`, { method: "DELETE" })
        : send(base + "/reviews", body),
    onSuccess: () => {
      void cache.invalidateQueries();
    },
  });

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const values = new FormData(e.currentTarget);
    mutation.mutate({
      body: {
        rating: Number(values.get("rating")),
        text: String(values.get("text")),
      },
    });
  }

  return (
    <section className={d.section} id="reviews">
      <div className={d.sectionHeading}>
        <h2>
          Community reviews{" "}
          {!loading && !error && (
            <span className="muted">{reviews?.length || 0}</span>
          )}
        </h2>
        {!loading && !error && (
          <button
            type="button"
            className="secondary"
            onClick={() => reviewInput.current?.focus()}
          >
            {mine ? "Edit your review" : "Write a review"}
          </button>
        )}
      </div>
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorPanel error={error} retry={retry} />
      ) : (
        <>
          {reviews?.map((review) => (
            <article className={s.review} key={review.id}>
              <div>
                <Contributor username={review.created_by} prefix="" />
                <span className={s.rating}>
                  <Star size={15} />
                  {review.rating}/5
                </span>
              </div>
              <p className={s.prose}>{review.text}</p>
              {review.created_at && (
                <time className={d.timestamp} dateTime={review.created_at}>
                  {new Date(review.created_at).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </time>
              )}
              {(user?.role === "admin" ||
                review.created_by === user?.username) && (
                <button
                  className="secondary"
                  aria-busy={mutation.isPending}
                  disabled={mutation.isPending}
                  onClick={() => mutation.mutate({ id: review.id })}
                >
                  Remove review
                </button>
              )}
            </article>
          ))}
          {!reviews?.length && (
            <p className="muted">Be the first to share your experience.</p>
          )}
          <form
            className={s.reviewForm}
            key={mine?.id || "new"}
            onSubmit={submit}
          >
            <h3>{mine ? "Your review" : "What did you think?"}</h3>
            <label>
              Rating
              <select name="rating" defaultValue={mine?.rating || 5}>
                {[5, 4, 3, 2, 1].map((n) => (
                  <option key={n} value={n}>
                    {n} out of 5
                  </option>
                ))}
              </select>
            </label>
            <label>
              Your experience
              <textarea
                ref={reviewInput}
                name="text"
                defaultValue={mine?.text || ""}
                placeholder="What was useful? Who would you recommend it to?"
              />
            </label>
            <button
              aria-busy={mutation.isPending}
              disabled={mutation.isPending}
            >
              {mine ? "Update review" : "Share review"}
            </button>
            {mutation.error && <p role="alert">{humanError(mutation.error)}</p>}
            {mutation.isSuccess && (
              <p role="status" className="muted">
                Your change has been saved.
              </p>
            )}
          </form>{" "}
        </>
      )}
    </section>
  );
}
