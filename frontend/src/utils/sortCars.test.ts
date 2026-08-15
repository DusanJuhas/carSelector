import { describe, expect, it } from 'vitest';
import { sortCars } from './sortCars';
import type { Car } from '../types';

function makeCar(id: string, make: string, model: string, trim: string, amount: number): Car {
  return {
    id,
    make,
    model,
    trim,
    price: { amount, currency: 'CZK' },
    score: null,
    specs: [],
    flag: null,
  };
}

const cheap = makeCar('1', 'Škoda', 'Fabia', 'Classic', 450000);
const mid = makeCar('2', 'Mazda', 'CX-5', 'Prime-Line', 824900);
const expensive = makeCar('3', 'Škoda', 'Superb', 'Laurin & Klement', 1360000);
const cars = [mid, expensive, cheap];

describe('sortCars', () => {
  it('leaves the order untouched for "recommended"', () => {
    expect(sortCars(cars, 'recommended')).toEqual(cars);
  });

  it('sorts ascending by price', () => {
    expect(sortCars(cars, 'price_asc').map((c) => c.id)).toEqual(['1', '2', '3']);
  });

  it('sorts descending by price', () => {
    expect(sortCars(cars, 'price_desc').map((c) => c.id)).toEqual(['3', '2', '1']);
  });

  it('sorts alphabetically by make, model, trim', () => {
    expect(sortCars(cars, 'alpha').map((c) => c.id)).toEqual(['2', '1', '3']);
  });

  it('does not mutate the input array', () => {
    const copy = [...cars];
    sortCars(cars, 'price_asc');
    expect(cars).toEqual(copy);
  });

  it('orders by the given custom sequence', () => {
    expect(sortCars(cars, 'custom', ['3', '1', '2']).map((c) => c.id)).toEqual(['3', '1', '2']);
  });

  it('appends cars missing from the custom order at the end, keeping their relative order', () => {
    // Only "1" is placed - "2" and "3" should follow in their original relative order.
    expect(sortCars(cars, 'custom', ['1']).map((c) => c.id)).toEqual(['1', '2', '3']);
  });

  it('falls back to input order when no custom order is given', () => {
    expect(sortCars(cars, 'custom').map((c) => c.id)).toEqual(['2', '3', '1']);
  });
});
