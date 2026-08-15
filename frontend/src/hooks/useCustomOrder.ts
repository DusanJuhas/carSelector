import { useCallback, useState } from 'react';

const STORAGE_KEY = 'rovis.customCarOrder';

/**
 * Args:
 *   None.
 *
 * Returns:
 *   The persisted order (car ids, most-preferred first) if
 *   `localStorage` has one and it parses as a string array; `[]`
 *   otherwise (no order yet, or `localStorage` unavailable/corrupt).
 */
function readStoredOrder(): string[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((id): id is string => typeof id === 'string') : [];
  } catch {
    return [];
  }
}

export interface UseCustomOrderResult {
  customOrder: string[];
  setCustomOrder: (ids: string[]) => void;
}

/**
 * Persists the "Moje pořadí" (my order) sort option's drag-reordered car
 * sequence across reloads via `localStorage`. Session-wide rather than
 * scoped to one conversation/catalog page, since it represents the user's
 * own preference, not server state.
 *
 * @returns The current order plus a setter that also persists it - see
 *   `UseCustomOrderResult`.
 */
export function useCustomOrder(): UseCustomOrderResult {
  const [customOrder, setCustomOrderState] = useState<string[]>(readStoredOrder);

  const setCustomOrder = useCallback((ids: string[]) => {
    setCustomOrderState(ids);
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
    } catch {
      // Best-effort persistence only - localStorage may be disabled/full;
      // the in-memory order for this session still works either way.
    }
  }, []);

  return { customOrder, setCustomOrder };
}
