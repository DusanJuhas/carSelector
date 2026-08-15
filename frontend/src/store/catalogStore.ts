import { create } from 'zustand';
import type { Car } from '../types';

/**
 * Holds the "browsing mode" catalog page(s) loaded so far - pure state
 * (setters only), same split as `conversationStore`: side effects (the
 * actual `GET /vehicles` calls) live in `hooks/useCatalog.ts`.
 */
interface CatalogState {
  cars: Car[];
  page: number;
  pageSize: number;
  total: number;
  /** Replaces the loaded cars with a single page (the initial load). */
  setPage: (cars: Car[], page: number, pageSize: number, total: number) => void;
  /** Appends one more page's cars to what's already loaded (for "load more"). */
  appendPage: (cars: Car[], page: number, total: number) => void;
}

export const useCatalogStore = create<CatalogState>((set) => ({
  cars: [],
  page: 0,
  pageSize: 20,
  total: 0,
  setPage: (cars, page, pageSize, total) => set({ cars, page, pageSize, total }),
  appendPage: (cars, page, total) =>
    set((state) => ({ cars: [...state.cars, ...cars], page, total })),
}));
