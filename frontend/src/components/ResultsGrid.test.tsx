import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ResultsGrid } from './ResultsGrid';
import type { Car } from '../types';

const cars: Car[] = [
  { id: 'a', make: 'Subaru', model: 'Outback', trim: 'Wilderness', price: { amount: 811000, currency: 'CZK' }, score: 93, specs: ['4×4'], flag: null },
];

const twoCars: Car[] = [
  cars[0],
  { id: 'b', make: 'Toyota', model: 'RAV4', trim: 'Comfort', price: { amount: 950000, currency: 'CZK' }, score: 88, specs: ['AWD'], flag: null },
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

  it('is not draggable by default', () => {
    const { container } = render(<ResultsGrid cars={twoCars} />);
    const grid = container.querySelector('.grid')!;
    expect(grid.children[0]).toHaveAttribute('draggable', 'false');
  });

  it('reports the new order once a card is dragged onto another', () => {
    const onReorder = vi.fn();
    const { container } = render(<ResultsGrid cars={twoCars} reorderable onReorder={onReorder} />);
    const grid = container.querySelector('.grid')!;
    const [firstWrapper, secondWrapper] = Array.from(grid.children);

    expect(firstWrapper).toHaveAttribute('draggable', 'true');

    fireEvent.dragStart(firstWrapper);
    fireEvent.dragOver(secondWrapper);
    fireEvent.drop(secondWrapper);

    expect(onReorder).toHaveBeenCalledWith(['b', 'a']);
  });
});
