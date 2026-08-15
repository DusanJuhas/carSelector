import { useEffect, useState } from 'react';
import { getVehicleDetail } from '../api/vehicleDetail';
import type { VehicleDetail } from '../types';

export interface UseVehicleDetailResult {
  detail: VehicleDetail | null;
  isLoading: boolean;
  /** True if the fetch failed (not found, or unreachable backend). */
  error: boolean;
}

/**
 * Loads full detail for one vehicle configuration, re-fetching whenever
 * `configurationId` changes. A no-op while `configurationId` is `null`
 * (the detail modal isn't open yet) - `CarCard`/`ResultsGrid` only ever
 * pass a real id once the user has actually clicked a card.
 *
 * @param configurationId - The configuration id to load, or `null` to
 *   stay idle.
 * @returns The loaded detail plus loading/error state - see
 *   `UseVehicleDetailResult`.
 */
export function useVehicleDetail(configurationId: string | null): UseVehicleDetailResult {
  const [detail, setDetail] = useState<VehicleDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (configurationId === null) {
      setDetail(null);
      setError(false);
      return;
    }

    let cancelled = false;
    setDetail(null);
    setIsLoading(true);
    setError(false);
    getVehicleDetail(configurationId)
      .then((result) => {
        if (!cancelled) setDetail(result);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [configurationId]);

  return { detail, isLoading, error };
}
