import { apiClient, toApiError } from './client';
import { toCar } from './vehicleSummary';
import type { VehicleSummaryDTO } from './vehicleSummary';
import type {
  ColorFinish,
  ColorOption,
  ConsumptionUnit,
  Drivetrain,
  FuelType,
  OptionCategory,
  OptionLine,
  PowertrainSpec,
  PricePoint,
  VehicleDetail,
} from '../types';
import type { Money } from '../types';

/** Wire shape of `backend/app/schemas/vehicle.py`'s `PowertrainSpec`. */
interface PowertrainSpecDTO {
  fuel_type: FuelType;
  transmission: string | null;
  drivetrain: Drivetrain;
  power_kw: number | null;
  power_hp: number | null;
  consumption_min: number | null;
  consumption_max: number | null;
  consumption_unit: ConsumptionUnit | null;
  co2_min_g_km: number | null;
  co2_max_g_km: number | null;
}

/** Wire shape of `backend/app/schemas/vehicle.py`'s `ColorOption`. */
interface ColorOptionDTO {
  name: string;
  finish_type: ColorFinish | null;
  surcharge: Money;
}

/** Wire shape of `backend/app/schemas/vehicle.py`'s `OptionLine`. */
interface OptionLineDTO {
  name: string;
  category: OptionCategory;
  surcharge: Money;
}

/** Wire shape of `backend/app/schemas/vehicle.py`'s `PricePoint`. */
interface PricePointDTO {
  valid_from: string;
  valid_to: string | null;
  price: Money;
  lowest_price_30d: Money | null;
}

/** Wire shape of `GET /api/vehicles/{configuration_id}`'s response (doc/api-contract.md's `VehicleDetail`). */
interface VehicleDetailDTO extends VehicleSummaryDTO {
  powertrain: PowertrainSpecDTO;
  colors: ColorOptionDTO[];
  standard_equipment: string[];
  optional_equipment: OptionLineDTO[];
  price_history: PricePointDTO[];
}

/**
 * Maps the backend's `VehicleDetail` onto the frontend's camelCase
 * `VehicleDetail` shape, reusing `toCar` for the fields shared with the
 * summary/card view.
 *
 * @param dto - The full detail payload for one configuration.
 * @returns The equivalent frontend `VehicleDetail`.
 */
function toVehicleDetail(dto: VehicleDetailDTO): VehicleDetail {
  const powertrain: PowertrainSpec = {
    fuelType: dto.powertrain.fuel_type,
    transmission: dto.powertrain.transmission,
    drivetrain: dto.powertrain.drivetrain,
    powerKw: dto.powertrain.power_kw,
    powerHp: dto.powertrain.power_hp,
    consumptionMin: dto.powertrain.consumption_min,
    consumptionMax: dto.powertrain.consumption_max,
    consumptionUnit: dto.powertrain.consumption_unit,
    co2MinGKm: dto.powertrain.co2_min_g_km,
    co2MaxGKm: dto.powertrain.co2_max_g_km,
  };

  const colors: ColorOption[] = dto.colors.map((color) => ({
    name: color.name,
    finishType: color.finish_type,
    surcharge: color.surcharge,
  }));

  const optionalEquipment: OptionLine[] = dto.optional_equipment.map((option) => ({
    name: option.name,
    category: option.category,
    surcharge: option.surcharge,
  }));

  const priceHistory: PricePoint[] = dto.price_history.map((point) => ({
    validFrom: point.valid_from,
    validTo: point.valid_to,
    price: point.price,
    lowestPrice30d: point.lowest_price_30d,
  }));

  return {
    ...toCar(dto),
    powertrain,
    colors,
    standardEquipment: dto.standard_equipment,
    optionalEquipment,
    priceHistory,
  };
}

/**
 * Fetches full detail for one vehicle configuration - everything
 * `CarCard`'s summary doesn't carry (powertrain specs, color/option
 * surcharges, price history).
 *
 * @param configurationId - The configuration id (`Car.id`, numeric but
 *   carried as a string on the frontend).
 * @returns The vehicle's full detail.
 * @throws {ApiError} `"vehicle_not_found"` if the id doesn't exist,
 *   `"network_error"` if the backend isn't reachable.
 */
export async function getVehicleDetail(configurationId: string): Promise<VehicleDetail> {
  try {
    const { data } = await apiClient.get<VehicleDetailDTO>(`/vehicles/${configurationId}`);
    return toVehicleDetail(data);
  } catch (error) {
    throw toApiError(error);
  }
}
