import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { CarCard } from './CarCard';
import type { Car } from '../types';

const car: Car = {
  id: 'toyota-corolla-cross-hybrid-awd',
  make: 'Toyota',
  model: 'Corolla Cross Hybrid AWD',
  price: '$29,800',
  score: 97,
  specs: ['Hybrid', 'AWD'],
  flag: null,
  topPick: true,
};

describe('CarCard', () => {
  it('renders make, model, price and score', () => {
    render(<CarCard car={car} />);
    expect(screen.getByText('Toyota Corolla Cross Hybrid AWD')).toBeInTheDocument();
    expect(screen.getByText('$29,800')).toBeInTheDocument();
    expect(screen.getByText('97%')).toBeInTheDocument();
    expect(screen.getByText('Top match')).toBeInTheDocument();
  });

  it('shows a flag message when present', () => {
    render(<CarCard car={{ ...car, flag: 'Over budget by ~$2,200', topPick: false }} />);
    expect(screen.getByText('Over budget by ~$2,200')).toBeInTheDocument();
  });
});
