import type { Money } from './money';

export interface Car {
  id: string;
  make: string;
  model: string;
  trim: string;
  price: Money;
  /** Recommendation match score (0-100); null outside a narrowed/recommendation context (e.g. plain catalog browsing). */
  score: number | null;
  specs: string[];
  flag: string | null;
  topPick?: boolean;
  /** AI-generated, fact-grounded explanation; null outside a chat context or if the AI layer isn't configured. */
  explanation?: string | null;
}
