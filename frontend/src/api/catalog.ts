import { apiClient, toApiError } from './client';
import { toCar } from './vehicleSummary';
import type { Car } from '../types';
import type { VehicleSummaryDTO } from './vehicleSummary';

/** Wire shape of `GET /api/vehicles`'s response (doc/api-contract.md's `Page[VehicleSummary]`). */
interface VehiclePageDTO {
  items: VehicleSummaryDTO[];
  page: number;
  page_size: number;
  total: number;
}

export interface ListVehiclesParams {
  /** 1-indexed page number. Defaults to 1. */
  page?: number;
  /** Rows per page. Defaults to the backend's own default (20). */
  pageSize?: number;
}

export interface ListVehiclesResult {
  cars: Car[];
  page: number;
  pageSize: number;
  /** Total matching rows across all pages, not just `cars.length` - compare against it to know whether more pages exist. */
  total: number;
}

/**
 * Lists the catalog directly - no AI, no conversation involved. This is
 * "browsing mode" (see `ChatPage`): the default view before the AI has
 * narrowed anything, and the only vehicle data available at all when
 * `ANTHROPIC_API_KEY` isn't configured on the backend.
 *
 * @param params - Pagination.
 * @returns One page of the catalog.
 * @throws {ApiError} `"network_error"` if the backend isn't reachable.
 */
export async function listVehicles(params: ListVehiclesParams = {}): Promise<ListVehiclesResult> {
  try {
    const { data } = await apiClient.get<VehiclePageDTO>('/vehicles', {
      params: { page: params.page, page_size: params.pageSize },
    });
    return {
      cars: data.items.map(toCar),
      page: data.page,
      pageSize: data.page_size,
      total: data.total,
    };
  } catch (error) {
    throw toApiError(error);
  }
}
