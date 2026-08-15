import type { Car, Money } from '../types';

/**
 * Wire shape of one `VehicleSummary` (doc/api-contract.md) - shared by
 * `POST .../messages`'s `vehicles` array and `GET /vehicles`'s `items`,
 * see `conversation.ts` and `catalog.ts`.
 */
export interface VehicleSummaryDTO {
  configuration_id: number;
  brand: string;
  model: string;
  trim: string;
  price: Money;
  match_score: number | null;
  specs: string[];
  flag: string | null;
  top_pick: boolean;
  thumbnail_url: string | null;
  explanation: string | null;
}

/**
 * Maps one backend `VehicleSummary` onto the frontend's display-oriented
 * `Car` shape.
 *
 * @param dto - One entry from a `vehicles`/`items` array.
 * @returns The equivalent `Car`. `id` is the configuration id as a
 *   string (`Car.id` is a generic string identifier). `score` is
 *   `match_score` passed through as-is - it's `null` outside a narrowed/
 *   recommendation context (e.g. `GET /vehicles`'s plain catalog
 *   listing), and `CarCard` hides the score badge when it's `null`
 *   rather than treating that as a real 0% match.
 */
export function toCar(dto: VehicleSummaryDTO): Car {
  return {
    id: String(dto.configuration_id),
    make: dto.brand,
    model: dto.model,
    trim: dto.trim,
    price: dto.price,
    score: dto.match_score,
    specs: dto.specs,
    flag: dto.flag,
    topPick: dto.top_pick,
    explanation: dto.explanation,
  };
}
