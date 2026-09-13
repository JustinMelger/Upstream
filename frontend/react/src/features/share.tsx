import { ResourceCard, type ResourcePreview } from "../components/resources";
import { useState, useRef, type FormEvent } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useParams, useSearchParams, useNavigate } from "react-router";
import { ArrowDown, ArrowUp, Plus, X } from "lucide-react";
import {
  api,
  send,
  plural,
  detailUrl,
  queryString,
  humanError,
  type ContentType,
  type Content,
  type CatalogItem,
  type Page,
} from "../lib/api/client";
import {
  Empty,
  ErrorPanel,
  Heading,
  Loading,
  Pagination,
} from "../components/ui";
import { useAuth } from "./auth";
import s from "./pages.module.css";
import { useCourseJourney } from "./course-journey";
import { useMetadata } from "./metadata";
import { useDraft } from "./drafts";
type PathItem = { type: string; id: number; title: string };
export function Share() {
  const { kind } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const type: ContentType =
    kind === "path"
      ? "path"
      : ["course", "article", "video"].includes(params.get("type") || "")
        ? (params.get("type") as ContentType)
        : "course";
  const edit = Number(params.get("edit")) || 0;
  const { user } = useAuth();
  const query = useQuery({
    queryKey: ["detail", type, edit],
    queryFn: () => api<Content>(`/${plural(type)}/${edit}`),
    enabled: edit > 0,
  });
  if (kind !== "item" && kind !== "path")
    return (
      <Empty title="Choose something to share.">
        Open the Share menu to add a learning item or path.
      </Empty>
    );
  if (edit && query.isPending) return <Loading />;
  if (query.error)
    return (
      <ErrorPanel error={query.error} retry={() => void query.refetch()} />
    );
  if (
    edit &&
    user?.role !== "admin" &&
    query.data?.created_by !== user?.username
  )
    return (
      <Empty title="You can’t edit this item.">
        Only its owner or an administrator can make changes.
      </Empty>
    );
  return (
    <>
      <Heading
        title={
          edit ? "Edit your shared learning" : "Found something worth sharing?"
        }
      >
        Pass it on. Someone here will be glad you did.
      </Heading>
      {!edit && (
        <div className={s.tabs} aria-label="Resource type">
          {(["course", "article", "video", "path"] as const).map((value) => (
            <button
              key={value}
              aria-pressed={type === value}
              className={type === value ? s.active : ""}
              onClick={() =>
                navigate(
                  value === "path"
                    ? "/share/path"
                    : `/share/item?type=${value}`,
                )
              }
            >
              {value[0].toUpperCase() + value.slice(1)}
            </button>
          ))}
        </div>
      )}
      <ShareForm
        key={`${type}:${edit}`}
        type={type}
        content={query.data}
        edit={edit}
      />
    </>
  );
}
function ShareForm({
  type,
  content,
  edit,
}: {
  type: ContentType;
  content?: Content;
  edit: number;
}) {
  const navigate = useNavigate(),
    cache = useQueryClient();
  const journey = useCourseJourney();
  const [items, setItems] = useState<PathItem[]>(content?.items || []);
  const { user } = useAuth();
  const formRef = useRef<HTMLFormElement>(null);
  const draft = useDraft(
    user!.username,
    `${type}:${edit || "new"}`,
    formRef,
    items,
  );
  const [noteLength, setNoteLength] = useState(
    content?.recommendation_note?.length || 0,
  );
  const initialPreview = {
    title: content?.title || content?.name || "",
    description: content?.description || "",
    recommendation_note: content?.recommendation_note || "",
  };
  const [previewValues, setPreviewValues] = useState(initialPreview);
  function refreshPreview() {
    const value = (name: string) =>
      (formRef.current?.elements.namedItem(name) as HTMLInputElement | null)
        ?.value || "";
    setPreviewValues({
      title: value(type === "path" ? "name" : "title"),
      description: value("description"),
      recommendation_note: value("recommendation_note"),
    });
  }
  const metadata = useMetadata(formRef, () => {
    draft.changed();
    refreshPreview();
  });
  const preview: ResourcePreview = {
    ...previewValues,
    title: previewValues.title.trim() || "Your next shared find",
    type,
    created_by: content?.created_by || user!.username,
  };
  const previewContent = (
    <>
      <ResourceCard item={preview} preview />
      {type === "path" && (
        <p className="muted">
          {items.length} {items.length === 1 ? "item" : "items"} in your
          learning sequence
        </p>
      )}
    </>
  );
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [announcement, setAnnouncement] = useState("");

  const mutation = useMutation({
    mutationFn: (body: unknown) =>
      send<Content>(
        `/${plural(type)}${edit ? `/${edit}` : ""}`,
        body,
        edit ? "PUT" : "POST",
      ),
    onSuccess: (result) => {
      draft.complete();
      if (edit) journey.show({ message: "Changes saved." });
      else if (type === "course")
        journey.show({
          message: "Course shared. Add it to My learning when you’re ready.",
        });
      void cache.invalidateQueries();
      navigate(detailUrl(type, Number(result.id)));
    },
  });
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    metadata.cancel();
    const form = e.currentTarget;
    const invalid: Record<string, string> = {};
    for (const field of Array.from(form.elements)) {
      if (
        field instanceof HTMLInputElement ||
        field instanceof HTMLTextAreaElement ||
        field instanceof HTMLSelectElement
      ) {
        if (!field.checkValidity())
          invalid[field.name] = field.validationMessage;
        else if (field.required && !field.value.trim())
          invalid[field.name] = "Please enter a value.";
      }
    }
    const note = form.elements.namedItem(
      "recommendation_note",
    ) as HTMLTextAreaElement;
    if (note.value.length > 1000)
      invalid.recommendation_note = "Use 1,000 characters or fewer.";
    if (
      type === "article" &&
      (form.elements.namedItem("description") as HTMLTextAreaElement).value
        .length > 2000
    )
      invalid.description = "Use 2,000 characters or fewer.";
    setErrors(invalid);
    if (Object.keys(invalid).length) {
      const field = form.elements.namedItem(
        Object.keys(invalid)[0],
      ) as HTMLElement;
      const details = field?.closest("details");
      if (details) details.open = true;
      field?.focus();
      return;
    }
    const values = Object.fromEntries(new FormData(form));
    const body: Record<string, unknown> = {
      ...values,
      recommendation_note:
        String(values.recommendation_note || "").trim() || null,
    };
    if (type === "path") {
      body.items = items.map(({ type, id }, position) => ({
        type,
        id,
        position,
      }));
    }
    if (type === "course") {
      body.duration_hours = values.duration_hours
        ? Number(values.duration_hours)
        : null;
    }
    mutation.mutate(body);
  }
  function move(index: number, delta: number) {
    draft.changed();
    setAnnouncement(
      `${items[index].title} moved to position ${index + delta + 1} of ${items.length}.`,
    );
    setItems((old) => {
      const next = [...old];
      [next[index], next[index + delta]] = [next[index + delta], next[index]];
      return next;
    });
  }
  return (
    <div className={s.shareLayout}>
      <form
        ref={formRef}
        className={s.shareForm}
        onSubmit={submit}
        noValidate
        onInput={(e) => {
          draft.changed();
          refreshPreview();
          const field = e.target as HTMLInputElement;
          metadata.changed(field.name);
          if (field.name === "recommendation_note")
            setNoteLength(field.value.length);
          setErrors((old) => {
            const next = { ...old };
            delete next[field.name];
            return next;
          });
        }}
      >
        {draft.unavailable && (
          <p role="status" className={s.notice}>
            Draft recovery is unavailable in this browser. Keep this page open
            until you publish.
          </p>
        )}
        {draft.candidate && (
          <section className={s.notice} aria-label="Saved draft">
            <h2>You have an unfinished draft.</h2>
            <p>
              Restore your work or continue with{" "}
              {edit ? "the published version" : "a fresh form"}.
            </p>
            <div className={s.actions}>
              <button
                type="button"
                onClick={() => {
                  metadata.cancel();
                  const saved = draft.restore();
                  if (saved) {
                    setItems(saved.items);
                    refreshPreview();
                    setNoteLength(
                      saved.values.recommendation_note?.length || 0,
                    );
                  }
                }}
              >
                Restore draft
              </button>
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  metadata.cancel();
                  draft.discard();
                }}
              >
                Discard draft
              </button>
            </div>
          </section>
        )}
        {Object.keys(errors).length > 0 && (
          <div role="alert" className={s.error}>
            <strong>Check the highlighted fields before publishing.</strong>
            <ul>
              {Object.entries(errors).map(([name, error]) => (
                <li key={name}>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() =>
                      (
                        formRef.current?.elements.namedItem(name) as HTMLElement
                      )?.focus()
                    }
                  >
                    {name.replaceAll("_", " ")}: {error}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
        <fieldset
          disabled={!!draft.candidate || mutation.isPending}
          className={s.formFields}
        >
          <section className={s.panel}>
            <h2>
              {type === "path"
                ? "Give your path a direction"
                : "The essentials"}
            </h2>

            {type !== "path" && (
              <div className={!edit ? s.resourceUrl : undefined}>
                <label>
                  Resource URL
                  <input
                    name="url"
                    aria-invalid={!!errors.url}
                    aria-describedby={errors.url ? "error-url" : undefined}
                    type="url"
                    required
                    defaultValue={content?.url || ""}
                    placeholder="https://…"
                  />
                  {errors.url && (
                    <small id="error-url" className={s.fieldError}>
                      {errors.url}
                    </small>
                  )}
                </label>
                {!edit && (
                  <div className={s.metadataAction}>
                    <button
                      type="button"
                      className="secondary"
                      disabled={metadata.pending}
                      aria-busy={metadata.pending}
                      onClick={() => void metadata.fetchDetails()}
                    >
                      {metadata.pending ? "Fetching details…" : "Fetch details"}
                    </button>
                    <p role="status" aria-live="polite">
                      {metadata.message}
                    </p>
                    {metadata.error && (
                      <p role="alert" className={s.error}>
                        {metadata.error}
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}
            <label>
              {type === "path" ? "Path name" : "Title"}
              <input
                aria-invalid={!!errors[type === "path" ? "name" : "title"]}
                name={type === "path" ? "name" : "title"}
                required
                defaultValue={content?.title || content?.name || ""}
              />
              {errors[type === "path" ? "name" : "title"] && (
                <small className={s.fieldError}>
                  {errors[type === "path" ? "name" : "title"]}
                </small>
              )}
            </label>
            <label>
              What will people learn?
              <textarea
                name="description"
                aria-label="What will people learn?"
                maxLength={type === "article" ? 2000 : undefined}
                aria-invalid={!!errors.description}
                aria-describedby={
                  errors.description ? "error-description" : undefined
                }
                required={type === "course"}
                defaultValue={content?.description || ""}
                placeholder="What will someone learn?"
              />
              {errors.description && (
                <small id="error-description" className={s.fieldError}>
                  {errors.description}
                </small>
              )}
            </label>
          </section>
          <details className={s.mobilePreview}>
            <summary>Preview your share</summary>
            {previewContent}
          </details>
          <section className={s.panel}>
            <label>
              Why do you recommend it?{" "}
              <span className="muted">
                Optional · {noteLength}/1,000 characters
              </span>
              <textarea
                name="recommendation_note"
                aria-invalid={!!errors.recommendation_note}
                aria-describedby={
                  errors.recommendation_note
                    ? "error-recommendation_note"
                    : undefined
                }
                maxLength={1000}
                defaultValue={content?.recommendation_note || ""}
                placeholder="Who is this for, and what made it useful to you?"
              />
              {errors.recommendation_note && (
                <small id="error-recommendation_note" className={s.fieldError}>
                  {errors.recommendation_note}
                </small>
              )}
            </label>
          </section>
          {type !== "path" && (
            <details className={s.panel}>
              <summary>
                Additional details <span className="muted">Optional</span>
              </summary>
              <div className={s.optionalFields}>
                {type === "article" && (
                  <label>
                    Tags
                    <input
                      name="tags"
                      aria-invalid={!!errors.tags}
                      aria-describedby={errors.tags ? "error-tags" : undefined}
                      defaultValue={content?.tags || ""}
                      placeholder="Python, testing, APIs"
                    />
                    {errors.tags && (
                      <small id="error-tags" className={s.fieldError}>
                        {errors.tags}
                      </small>
                    )}
                  </label>
                )}
                {(type === "course" || type === "video") && (
                  <div className={s.twoFields}>
                    <label>
                      Provider
                      <input
                        name="provider"
                        aria-invalid={!!errors.provider}
                        aria-describedby={
                          errors.provider ? "error-provider" : undefined
                        }
                        defaultValue={content?.provider || ""}
                      />
                      {errors.provider && (
                        <small id="error-provider" className={s.fieldError}>
                          {errors.provider}
                        </small>
                      )}
                    </label>
                    <label>
                      Category
                      <input
                        name="category"
                        aria-invalid={!!errors.category}
                        aria-describedby={
                          errors.category ? "error-category" : undefined
                        }
                        defaultValue={content?.category || ""}
                      />
                      {errors.category && (
                        <small id="error-category" className={s.fieldError}>
                          {errors.category}
                        </small>
                      )}
                    </label>
                  </div>
                )}
                {type === "course" && (
                  <>
                    <div className={s.twoFields}>
                      <label>
                        Difficulty
                        <select
                          name="level"
                          aria-invalid={!!errors.level}
                          aria-describedby={
                            errors.level ? "error-level" : undefined
                          }
                          defaultValue={content?.level || ""}
                        >
                          <option value="">Not specified</option>
                          <option>Beginner</option>
                          <option>Intermediate</option>
                          <option>Advanced</option>
                        </select>
                        {errors.level && (
                          <small id="error-level" className={s.fieldError}>
                            {errors.level}
                          </small>
                        )}
                      </label>
                      <label>
                        Duration in hours
                        <input
                          name="duration_hours"
                          aria-invalid={!!errors.duration_hours}
                          aria-describedby={
                            errors.duration_hours
                              ? "error-duration_hours"
                              : undefined
                          }
                          type="number"
                          min="0"
                          step="0.25"
                          defaultValue={content?.duration_hours ?? ""}
                        />
                        {errors.duration_hours && (
                          <small
                            id="error-duration_hours"
                            className={s.fieldError}
                          >
                            {errors.duration_hours}
                          </small>
                        )}
                      </label>
                    </div>
                    <label>
                      Learning outcomes
                      <textarea
                        name="learning_outcomes"
                        aria-invalid={!!errors.learning_outcomes}
                        aria-describedby={
                          errors.learning_outcomes
                            ? "error-learning_outcomes"
                            : undefined
                        }
                        defaultValue={content?.learning_outcomes || ""}
                      />
                      {errors.learning_outcomes && (
                        <small
                          id="error-learning_outcomes"
                          className={s.fieldError}
                        >
                          {errors.learning_outcomes}
                        </small>
                      )}
                    </label>
                    <label>
                      Prerequisites
                      <textarea
                        name="prerequisites"
                        aria-invalid={!!errors.prerequisites}
                        aria-describedby={
                          errors.prerequisites
                            ? "error-prerequisites"
                            : undefined
                        }
                        defaultValue={content?.prerequisites || ""}
                      />
                      {errors.prerequisites && (
                        <small
                          id="error-prerequisites"
                          className={s.fieldError}
                        >
                          {errors.prerequisites}
                        </small>
                      )}
                    </label>
                    <label>
                      Language
                      <input
                        name="language"
                        aria-invalid={!!errors.language}
                        aria-describedby={
                          errors.language ? "error-language" : undefined
                        }
                        defaultValue={content?.language || ""}
                      />
                      {errors.language && (
                        <small id="error-language" className={s.fieldError}>
                          {errors.language}
                        </small>
                      )}
                    </label>
                  </>
                )}
              </div>
            </details>
          )}
          <p role="status" className="sr-only">
            {announcement}
          </p>
          {type === "path" && (
            <section className={s.panel}>
              <h2>Build the learning sequence</h2>
              <p className="muted">
                Mix courses, articles, and videos. Put them in the order you’d
                recommend.
              </p>
              <ol className={s.pathList}>
                {items.map((item, index) => (
                  <li key={`${item.type}:${item.id}`}>
                    <span>{index + 1}</span>
                    <div>
                      <small className="muted">{item.type}</small>
                      {item.title}
                    </div>
                    <button
                      type="button"
                      className="secondary"
                      aria-label={`Move ${item.title} up`}
                      disabled={index === 0}
                      onClick={() => move(index, -1)}
                    >
                      <ArrowUp size={15} />
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      aria-label={`Move ${item.title} down`}
                      disabled={index === items.length - 1}
                      onClick={() => move(index, 1)}
                    >
                      <ArrowDown size={15} />
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      aria-label={`Remove ${item.title}`}
                      onClick={() => {
                        draft.changed();
                        setItems((old) => old.filter((_, i) => i !== index));
                      }}
                    >
                      <X size={15} />
                    </button>
                  </li>
                ))}
              </ol>
              <ItemPicker
                selected={items}
                add={(item) => {
                  draft.changed();
                  setItems((old) => [...old, item]);
                }}
              />
            </section>
          )}
          {mutation.error && (
            <p role="alert" className={s.error}>
              {humanError(mutation.error)}
            </p>
          )}
          <div className={s.actions}>
            <button
              aria-busy={mutation.isPending}
              disabled={mutation.isPending}
            >
              {mutation.isPending
                ? "Saving…"
                : edit
                  ? "Save changes"
                  : "Share " + type}
            </button>
            <Link
              className="button secondary"
              to={edit ? detailUrl(type, edit) : "/explore"}
            >
              Cancel
            </Link>
          </div>
          <button
            type="button"
            className="secondary"
            onClick={() => {
              metadata.cancel();
              draft.discard();
              formRef.current?.reset();
              setItems(content?.items || []);
              setNoteLength(content?.recommendation_note?.length || 0);
              setErrors({});
              setPreviewValues(initialPreview);
            }}
          >
            Discard draft
          </button>
        </fieldset>
        {!draft.unavailable && (
          <p className={s.draftStatus} role="status">
            {draft.saveState === "saved"
              ? "Draft saved in this tab"
              : draft.saveState === "pending"
                ? "Saving draft…"
                : "Drafts stay in this tab until you publish, discard, or sign out."}
          </p>
        )}
      </form>
      <aside className={s.desktopPreview} aria-label="Publication preview">
        <h2>How it will appear</h2>
        {previewContent}
      </aside>
    </div>
  );
}
function ItemPicker({
  selected,
  add,
}: {
  selected: PathItem[];
  add: (item: PathItem) => void;
}) {
  const [q, setQ] = useState(""),
    [page, setPage] = useState(1),
    [type, setType] = useState("course");
  const query = useQuery({
    queryKey: ["picker", q, type, page],
    queryFn: ({ signal }) =>
      api<Page<CatalogItem>>(
        "/catalog?" + queryString({ q, type, page, page_size: 6 }),
        { signal },
      ),
  });
  return (
    <div className={s.picker}>
      <div className={s.twoFields}>
        <label>
          Find learning items
          <input
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
            placeholder="Search the library"
          />
        </label>
        <label>
          Item type
          <select
            value={type}
            onChange={(e) => {
              setType(e.target.value);
              setPage(1);
            }}
          >
            <option value="course">Courses</option>
            <option value="article">Articles</option>
            <option value="video">Videos</option>
          </select>
        </label>
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorPanel error={query.error} retry={() => void query.refetch()} />
      ) : (
        <>
          {query.data.items.map((item) => (
            <div className={s.pickerRow} key={item.id}>
              <span>{item.title}</span>
              <button
                type="button"
                className="secondary"
                disabled={selected.some(
                  (i) => i.type === item.type && i.id === item.id,
                )}
                onClick={() =>
                  add({ type: item.type, id: item.id, title: item.title })
                }
              >
                <Plus size={15} />
                Add
              </button>
            </div>
          ))}
          <Pagination
            page={page}
            pageSize={6}
            total={query.data.total}
            onChange={setPage}
          />
        </>
      )}
    </div>
  );
}
