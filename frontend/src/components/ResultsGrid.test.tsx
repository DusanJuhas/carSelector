import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
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

  it('passes onSelectCar through to each card', async () => {
    const onSelectCar = vi.fn();
    render(<ResultsGrid cars={cars} onSelectCar={onSelectCar} />);
    await userEvent.click(screen.getByRole('button'));
    expect(onSelectCar).toHaveBeenCalledWith(cars[0]);
  });
});
