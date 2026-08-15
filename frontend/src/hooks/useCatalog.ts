import { useCallback, useEffect, useRef, useState } from 'react';
import { useCatalogStore } from '../store/catalogStore';
import { listVehicles } from '../api/catalog';
import type { BackendSortOption, Car } from '../types';

const PAGE_SIZE = 20;

/** Sentinel distinct from any real `BackendSortOption | undefined` value, so the first render always fetches. */
const NEVER_FETCHED = Symbol('never-fetched');

export interface UseCatalogResult {
  cars: Car[];
  total: number;
  /** True only while the very first page is loading. */
  isLoading: boolean;
  /** True while an additional page (triggered by `loadMore`) is loading. */
  isLoadingMore: boolean;
  /** True if `cars.length < total` - whether `loadMore` would return anything. */
  hasMore: boolean;
  loadMore: () => void;
  /** True if the initial load failed (network/backend unreachable). */
  error: boolean;
}

/**
 * Loads the catalog directly for "browsing mode" (see `ChatPage`) - the
 * default view before the AI has narrowed anything, paginated rather
 * than loading all ~450 vehicles at once.
 *
 * @param sort - Server-side ordering (`SortControl`'s `price_asc` |
 *   `price_desc` | `alpha`); omit/`undefined` for the default order.
 *   Sorting must happen on the backend here (not client-side, unlike
 *   narrowed mode) since only one page is loaded at a time - see
 *   `types/sort.ts`.
 * @returns The cars loaded so far plus pagination state/actions - see
 *   `UseCatalogResult`.
 */
export function useCatalog(sort?: BackendSortOption): UseCatalogResult {
  const cars = useCatalogStore((state) => state.cars);
  const page = useCatalogStore((state) => state.page);
  const pageSize = useCatalogStore((state) => state.pageSize);
  const total = useCatalogStore((state) => state.total);
  const setPage = useCatalogStore((state) => state.setPage);
  const appendPage = useCatalogStore((state) => state.appendPage);

  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState(false);

  // Loads page 1 on mount, and again whenever `sort` actually changes
  // (resetting back to page 1 - a sort order only pushed to the pages
  // loaded so far would be wrong). Keyed on `sort` rather than a plain
  // boolean ref so StrictMode's dev-only double-invoke still only fetches
  // once per distinct sort value, not once per render.
  const lastFetchedSort = useRef<BackendSortOption | undefined | typeof NEVER_FETCHED>(NEVER_FETCHED);
  useEffect(() => {
    if (lastFetchedSort.current === sort) return;
    lastFetchedSort.current = sort;
    setIsLoading(true);
    setError(false);
    listVehicles({ page: 1, pageSize: PAGE_SIZE, sort })
      .then((result) => setPage(result.cars, result.page, result.pageSize, result.total))
      .catch(() => setError(true))
      .finally(() => setIsLoading(false));
  }, [sort, setPage]);

  const loadMore = useCallback(() => {
    if (isLoadingMore || cars.length >= total) return;
    setIsLoadingMore(true);
    listVehicles({ page: page + 1, pageSize, sort })
      .then((result) => appendPage(result.cars, result.page, result.total))
      .catch(() => setError(true))
      .finally(() => setIsLoadingMore(false));
  }, [isLoadingMore, cars.length, total, page, pageSize, sort, appendPage]);

  return {
    cars,
    total,
    isLoading,
    isLoadingMore,
    hasMore: cars.length < total,
    loadMore,
    error,
  };
}
