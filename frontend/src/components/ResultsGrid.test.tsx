import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ResultsGrid } from './ResultsGrid';
import type { Car } from '../types';

const cars: Car[] = [
  { id: 'a', make: 'Subaru', model: 'Outback', price: '$34,500', score: 93, specs: ['AWD'], flag: null },
];

describe('ResultsGrid', () => {
  it('shows an empty-state message when there are no cars', () => {
    render(<ResultsGrid cars={[]} />);
    expect(screen.getByText(/shortlist will appear here/i)).toBeInTheDocument();
  });

  it('renders a card per car', () => {
    render(<ResultsGrid cars={cars} />);
    expect(screen.getByText('Subaru Outback')).toBeInTheDocument();
  });
});
