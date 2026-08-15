import type { Car, SortOption } from '../types';

/**
 * Orders `cars` client-side for display. Used for every `SortOption` in
 * narrowed mode (the AI-narrowed shortlist is always fully loaded, so
 * client-side sorting is correct), and for `'custom'`/`'recommended'` in
 * browsing mode too - `'price_asc' | 'price_desc' | 'alpha'` in browsing
 * mode are instead pushed to the backend (see `hooks/useCatalog.ts`) since
 * only one page is loaded at a time, so this is a no-op for those there
 * (`'recommended'`, the default `ChatPage` passes in that case).
 *
 * @param cars - Cars to order; not mutated.
 * @param sort - The chosen ordering.
 * @param customOrder - Car ids in the user's manually dragged order (see
 *   `hooks/useCustomOrder.ts`); only consulted when `sort === 'custom'`.
 *   Cars not present in it keep their relative input order and sort after
 *   every car that is (stable sort, so a partially-arranged list is fine).
 * @returns A new array in the requested order; `cars` itself is untouched.
 */
export function sortCars(cars: Car[], sort: SortOption, customOrder: string[] = []): Car[] {
  switch (sort) {
    case 'price_asc':
      return [...cars].sort((a, b) => a.price.amount - b.price.amount);
    case 'price_desc':
      return [...cars].sort((a, b) => b.price.amount - a.price.amount);
    case 'alpha':
      return [...cars].sort((a, b) =>
        `${a.make} ${a.model} ${a.trim}`.localeCompare(`${b.make} ${b.model} ${b.trim}`, 'cs'),
      );
    case 'custom': {
      const position = new Map(customOrder.map((id, index) => [id, index]));
      return [...cars].sort((a, b) => {
        const positionA = position.has(a.id) ? position.get(a.id)! : Number.MAX_SAFE_INTEGER;
        const positionB = position.has(b.id) ? position.get(b.id)! : Number.MAX_SAFE_INTEGER;
        return positionA - positionB;
      });
    }
    case 'recommended':
    default:
      return cars;
  }
}
