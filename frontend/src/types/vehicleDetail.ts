import type { Car } from './car';
import type { Money } from './money';

/** Backend enum values (backend/app/models/enums.py) - translated for display via `enums.*` i18n keys. */
export type FuelType = 'petrol' | 'diesel' | 'hybrid' | 'mild_hybrid' | 'phev' | 'electric';
export type Drivetrain = 'fwd' | 'rwd' | 'awd';
export type ConsumptionUnit = 'l_100km' | 'kwh_100km';
export type ColorFinish = 'solid' | 'metallic' | 'pearlescent';
export type OptionCategory = 'equipment' | 'package' | 'warranty' | 'service';

export interface PowertrainSpec {
  fuelType: FuelType;
  transmission: string | null;
  drivetrain: Drivetrain;
  powerKw: number | null;
  powerHp: number | null;
  consumptionMin: number | null;
  consumptionMax: number | null;
  consumptionUnit: ConsumptionUnit | null;
  co2MinGKm: number | null;
  co2MaxGKm: number | null;
}

export interface ColorOption {
  name: string;
  finishType: ColorFinish | null;
  surcharge: Money;
}

export interface OptionLine {
  name: string;
  category: OptionCategory;
  surcharge: Money;
}

export interface PricePoint {
  validFrom: string;
  validTo: string | null;
  price: Money;
  lowestPrice30d: Money | null;
}

/** Full vehicle detail page shape - `Car` (the card/summary shape) plus everything only the detail view needs. */
export interface VehicleDetail extends Car {
  powertrain: PowertrainSpec;
  colors: ColorOption[];
  standardEquipment: string[];
  optionalEquipment: OptionLine[];
  priceHistory: PricePoint[];
}
