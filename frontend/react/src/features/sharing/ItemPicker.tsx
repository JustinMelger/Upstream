import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";

import { ErrorPanel, Loading, Pagination } from "../../components/ui";
import {
  api,
  type CatalogItem,
  type Page,
  queryString,
} from "../../lib/api/client";
import s from "../pages.module.css";

export type PathItem = { type: string; id: number; title: string };

export function ItemPicker({
  selected,
  add,
}: {
  selected: PathItem[];
  add: (item: PathItem) => void;
}) {
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [type, setType] = useState("course");
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
