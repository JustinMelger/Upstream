import { useCallback } from "react";
import { useSearchParams } from "react-router";

/**
 * Manage shareable list filters through the current URL's search parameters.
 *
 * Empty values remove filters. Filter changes reset pagination unless page is
 * explicitly supplied; replace updates the current history entry instead of
 * adding one. Changing type or view also removes the legacy tab parameter.
 */
export function useFilters() {
  const [params, setParams] = useSearchParams();
  const page = Math.max(1, Number(params.get("page")) || 1);
  const updateMany = useCallback(
    function updateMany(values: Record<string, string>, replace = false) {
      setParams(
        (old) => {
          const next = new URLSearchParams(old);

          for (const [key, value] of Object.entries(values)) {
            if (key === "type" || key === "view") next.delete("tab");
            if (value) next.set(key, value);
            else next.delete(key);
          }

          if (!("page" in values)) next.delete("page");

          return next;
        },
        { replace },
      );
    },
    [setParams],
  );
  const update = useCallback(
    (key: string, value: string, replace = false) =>
      updateMany({ [key]: value }, replace),
    [updateMany],
  );

  return {
    params,
    page,
    updateMany,
    update,
  };
}
