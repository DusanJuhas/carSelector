import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { CarCard } from './CarCard';
import type { Car } from '../types';
import { formatMoney } from '../utils/money';

const car: Car = {
  id: 'toyota-corolla-cross-hybrid-awd',
  make: 'Toyota',
  model: 'Corolla Cross Hybrid AWD',
  price: { amount: 700000, currency: 'CZK' },
  score: 97,
  specs: ['Hybrid', 'AWD'],
  flag: null,
  topPick: true,
};

describe('CarCard', () => {
  it('renders make, model, price and score', () => {
    render(<CarCard car={car} />);
    expect(screen.getByText('Toyota Corolla Cross Hybrid AWD')).toBeInTheDocument();
    // Intl.NumberFormat joins groups with a non-breaking space that testing-library's
    // whitespace normalizer doesn't treat as equivalent to a plain space, so match on
    // raw textContent instead of the (normalized) default text matcher.
    expect(
      screen.getByText((_, element) => element?.textContent === formatMoney(car.price)),
    ).toBeInTheDocument();
    expect(screen.getByText('97%')).toBeInTheDocument();
    expect(screen.getByText('Nejlepší shoda')).toBeInTheDocument();
  });

  it('shows a flag message when present', () => {
    render(<CarCard car={{ ...car, flag: 'Nad rozpočtem o ~52 000 Kč', topPick: false }} />);
    expect(screen.getByText('Nad rozpočtem o ~52 000 Kč')).toBeInTheDocument();
  });
});
