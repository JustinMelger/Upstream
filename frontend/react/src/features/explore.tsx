import { useQuery } from "@tanstack/react-query";
import { ChevronDown, Search, SlidersHorizontal, X } from "lucide-react";
import { Dialog, Popover } from "radix-ui";
import { useEffect, useState } from "react";
import { Link } from "react-router";

import { Spotlight } from "../components/resources";
import {
  ContentCard,
  Empty,
  ErrorPanel,
  Heading,
  Loading,
  Pagination,
} from "../components/ui";
import uiStyles from "../components/ui.module.css";
import {
  api,
  type CatalogItem,
  type Page,
  queryString,
} from "../lib/api/client";
import { useFilters } from "./filters";
import s from "./pages.module.css";

type Filters = {
  q: string;
  type: string;
  provider: string;
  category: string;
  author: string;
  sort: string;
};

function Facet({
  field,
  filters,
  onChange,
}: {
  field: "provider" | "category";
  filters: Filters;
  onChange: (value: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const label = field === "provider" ? "Provider" : "Category";
  const query = useQuery({
    queryKey: ["facets", field, filters, search, page],
    enabled: open,
    queryFn: ({ signal }) =>
      api<Page<string>>(
        "/catalog/facets?" +
          queryString({ ...filters, field, option_q: search, page }),
        { signal },
      ),
  });

  function choose(value: string) {
    onChange(value);
    setOpen(false);
  }

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger
        className={`secondary ${s.facetTrigger}`}
        aria-label={`${label}: ${filters[field] || "All"}`}
      >
        <span>{filters[field] || label}</span>
        <ChevronDown size={16} />
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          className={s.facet}
          sideOffset={8}
          collisionPadding={16}
        >
          <label>
            Search {label.toLowerCase()} options
            <input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <button
            type="button"
            className="secondary"
            onClick={() => choose("")}
          >
            All {field === "provider" ? "providers" : "categories"}
          </button>
          {query.isPending ? (
            <Loading />
          ) : query.error ? (
            <ErrorPanel
              error={query.error}
              retry={() => void query.refetch()}
            />
          ) : (
            <>
              {query.data.items.length ? (
                <select
                  size={5}
                  aria-label={`${label} options`}
                  value={filters[field]}
                  onChange={(e) => choose(e.target.value)}
                >
                  <option value="" disabled>
                    Choose {label.toLowerCase()}
                  </option>
                  {filters[field] &&
                    !query.data.items.includes(filters[field]) && (
                      <option value={filters[field]}>
                        {filters[field]} (selected)
                      </option>
                    )}
                  {query.data.items.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="muted">No matching options.</p>
              )}
              <Pagination
                page={page}
                total={query.data.total}
                onChange={setPage}
              />
            </>
          )}
          <Popover.Close className="secondary">Close</Popover.Close>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

function FilterControls({
  filters,
  change,
}: {
  filters: Filters;
  change: (key: string, value: string) => void;
}) {
  return (
    <>
      <Facet
        field="provider"
        filters={filters}
        onChange={(v) => change("provider", v)}
      />
      <Facet
        field="category"
        filters={filters}
        onChange={(v) => change("category", v)}
      />
      <label>
        Sort
        <select
          aria-label="Sort"
          value={filters.sort}
          onChange={(e) => change("sort", e.target.value)}
        >
          <option value="newest">Newest first</option>
          <option value="title">Title A–Z</option>
          <option value="rating">Highest rated</option>
        </select>
      </label>
    </>
  );
}

export function Explore() {
  const { params, page, update, updateMany } = useFilters();
  const filters: Filters = {
    q: params.get("q") || "",
    type:
      params.get("type") ||
      (
        {
          courses: "course",
          articles: "article",
          videos: "video",
          paths: "path",
        } as Record<string, string>
      )[params.get("tab") || ""] ||
      "",
    provider: params.get("provider") || "",
    category: params.get("category") || "",
    author: params.get("author") || "",
    sort: params.get("sort") || "newest",
  };
  const [search, setSearch] = useState(filters.q);
  const [drawer, setDrawer] = useState(false);
  const [pending, setPending] = useState(filters);
  useEffect(() => setSearch(filters.q), [filters.q]);
  useEffect(() => {
    if (search === filters.q) return;
    const timer = setTimeout(() => update("q", search, true), 300);

    return () => clearTimeout(timer);
  }, [search, filters.q, update]);
  const query = useQuery({
    queryKey: ["catalog", filters, page],
    queryFn: ({ signal }) =>
      api<Page<CatalogItem>>("/catalog?" + queryString({ ...filters, page }), {
        signal,
      }),
  });
  const eligible =
    page === 1 &&
    filters.sort === "newest" &&
    ![
      filters.q,
      search,
      filters.type,
      filters.provider,
      filters.category,
      filters.author,
    ].some(Boolean);
  const spotlight = eligible
    ? query.data?.items.find((item) => item.recommendation_note?.trim()) ||
      query.data?.items[0]
    : undefined;
  const gridItems =
    query.data?.items.filter((item) => item !== spotlight) || [];

  return (
    <>
      <Heading title="Explore">
        Good things to learn. Shared by your people.
      </Heading>
      <div className={s.discoveryControls}>
        <div className={s.controls}>
          <label className={s.search}>
            <Search size={18} />
            <input
              aria-label="Search learning"
              placeholder="What are you curious about?"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </label>
          <Dialog.Root
            open={drawer}
            onOpenChange={(value) => {
              if (value) setPending(filters);
              setDrawer(value);
            }}
          >
            <Dialog.Trigger className={`secondary ${s.mobileFilters}`}>
              <SlidersHorizontal size={18} />
              Filters
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className={uiStyles.overlay} />
              <Dialog.Content className={s.filterDrawer}>
                <Dialog.Title>Refine your discovery</Dialog.Title>
                <Dialog.Description>
                  Choose a provider, category, or sort order.
                </Dialog.Description>
                <FilterControls
                  filters={pending}
                  change={(key, value) =>
                    setPending((old) => ({ ...old, [key]: value }))
                  }
                />
                <div className={uiStyles.actions}>
                  <button
                    onClick={() => {
                      updateMany({
                        provider: pending.provider,
                        category: pending.category,
                        sort: pending.sort,
                      });
                      setDrawer(false);
                    }}
                  >
                    Apply filters
                  </button>
                  <Dialog.Close className="secondary">Cancel</Dialog.Close>
                </div>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
        </div>
        <div className={s.tabs} aria-label="Content types">
          {[
            ["", "All learning"],
            ["course", "Courses"],
            ["article", "Articles"],
            ["video", "Videos"],
            ["path", "Paths"],
          ].map(([value, label]) => (
            <button
              key={value}
              aria-pressed={filters.type === value}
              className={filters.type === value ? s.active : ""}
              onClick={() => update("type", value)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className={s.desktopFilters}>
        <FilterControls filters={filters} change={update} />
      </div>
      <div className={s.chips}>
        {(["q", "type", "provider", "category", "author"] as const)
          .filter((key) => filters[key])
          .map((key) => (
            <button
              key={key}
              className="secondary"
              aria-label={`Remove ${key} filter: ${filters[key]}`}
              onClick={() => update(key, "")}
            >
              {key === "q" ? "Search" : key}: {filters[key]}
              <X size={14} />
            </button>
          ))}
        {Object.entries(filters).some(([k, v]) => k !== "sort" && v) && (
          <Link to="/explore">Clear all</Link>
        )}
      </div>
      <div className={s.sectionLabel}>
        <h2>{eligible ? "Recently shared" : "Learning resources"}</h2>
        <span className="muted" aria-live="polite">
          {query.data
            ? `${query.data.total} ${query.data.total === 1 ? "resource" : "resources"}`
            : query.error
              ? "Results unavailable"
              : "Finding resources…"}
        </span>
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorPanel error={query.error} retry={() => void query.refetch()} />
      ) : (
        <>
          {spotlight && <Spotlight item={spotlight} />}
          {query.data.items.length ? (
            <div className={s.grid}>
              {gridItems.map((item) => (
                <ContentCard item={item} key={`${item.type}:${item.id}`} />
              ))}
            </div>
          ) : (
            <Empty title="Nothing matches just yet." action={false}>
              Try removing a filter or{" "}
              <Link to="/share/item">share a useful find</Link>.
            </Empty>
          )}
          <Pagination
            page={page}
            total={query.data.total}
            onChange={(p) => update("page", String(p))}
          />
        </>
      )}
    </>
  );
}
