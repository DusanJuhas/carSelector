import type { Money } from './money';

export interface Car {
  id: string;
  make: string;
  model: string;
  price: Money;
  score: number;
  specs: string[];
  flag: string | null;
  topPick?: boolean;
}
