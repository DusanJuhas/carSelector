/**
 * Full set of choices `SortControl` offers the user. `'recommended'` and
 * `'custom'` are always applied client-side (see `utils/sortCars.ts`);
 * `'price_asc' | 'price_desc' | 'alpha'` are pushed to the backend while
 * browsing the paginated catalog (see `api/catalog.ts`) since sorting only
 * the cars already loaded in the browser would be wrong once there's more
 * than one page - but applied client-side instead against an
 * already-fully-loaded AI-narrowed shortlist.
 */
export type SortOption = 'recommended' | 'price_asc' | 'price_desc' | 'alpha' | 'custom';

/** The subset of `SortOption` the backend's `GET /vehicles?sort=` accepts. */
export type BackendSortOption = Extract<SortOption, 'price_asc' | 'price_desc' | 'alpha'>;
