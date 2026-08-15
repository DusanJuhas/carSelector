import { useCallback, useEffect, useRef, useState } from 'react';
import { useCatalogStore } from '../store/catalogStore';
import { listVehicles } from '../api/catalog';
import type { Car } from '../types';

const PAGE_SIZE = 20;

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
 * @returns The cars loaded so far plus pagination state/actions - see
 *   `UseCatalogResult`.
 */
export function useCatalog(): UseCatalogResult {
  const cars = useCatalogStore((state) => state.cars);
  const page = useCatalogStore((state) => state.page);
  const pageSize = useCatalogStore((state) => state.pageSize);
  const total = useCatalogStore((state) => state.total);
  const setPage = useCatalogStore((state) => state.setPage);
  const appendPage = useCatalogStore((state) => state.appendPage);

  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState(false);

  // Loads the first page once on mount. Guarded the same way as
  // useConversation's begin() - StrictMode's dev-only double-invoke would
  // otherwise fetch page 1 twice.
  const hasStarted = useRef(false);
  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;
    setIsLoading(true);
    setError(false);
    listVehicles({ page: 1, pageSize: PAGE_SIZE })
      .then((result) => setPage(result.cars, result.page, result.pageSize, result.total))
      .catch(() => setError(true))
      .finally(() => setIsLoading(false));
  }, [setPage]);

  const loadMore = useCallback(() => {
    if (isLoadingMore || cars.length >= total) return;
    setIsLoadingMore(true);
    listVehicles({ page: page + 1, pageSize })
      .then((result) => appendPage(result.cars, result.page, result.total))
      .catch(() => setError(true))
      .finally(() => setIsLoadingMore(false));
  }, [isLoadingMore, cars.length, total, page, pageSize, appendPage]);

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
