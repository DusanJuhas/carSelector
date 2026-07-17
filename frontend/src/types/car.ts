export interface Car {
  id: string;
  make: string;
  model: string;
  price: string;
  score: number;
  specs: string[];
  flag: string | null;
  topPick?: boolean;
}
