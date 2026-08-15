import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ResultsGrid } from './ResultsGrid';
import type { Car } from '../types';

const cars: Car[] = [
  { id: 'a', make: 'Subaru', model: 'Outback', price: { amount: 811000, currency: 'CZK' }, score: 93, specs: ['4×4'], flag: null },
];

describe('ResultsGrid', () => {
  it('shows an empty-state message when there are no cars', () => {
    render(<ResultsGrid cars={[]} />);
    expect(screen.getByText(/váš užší výběr se zobrazí zde/i)).toBeInTheDocument();
  });

  it('renders a card per car', () => {
    render(<ResultsGrid cars={cars} />);
    expect(screen.getByText('Subaru Outback')).toBeInTheDocument();
  });
});
