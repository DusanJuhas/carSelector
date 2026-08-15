import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ResultsGrid } from './ResultsGrid';
import type { Car } from '../types';

const cars: Car[] = [
  { id: 'a', make: 'Subaru', model: 'Outback', trim: 'Wilderness', price: { amount: 811000, currency: 'CZK' }, score: 93, specs: ['4×4'], flag: null },
];

describe('ResultsGrid', () => {
  it('shows an empty-state message when there are no cars', () => {
    render(<ResultsGrid cars={[]} />);
    expect(screen.getByText(/zatím nic nevyhovuje/i)).toBeInTheDocument();
  });

  it('renders a card per car', () => {
    render(<ResultsGrid cars={cars} />);
    expect(screen.getByText('Subaru Outback Wilderness')).toBeInTheDocument();
  });
});
