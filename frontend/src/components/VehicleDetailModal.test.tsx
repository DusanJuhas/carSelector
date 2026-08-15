import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { VehicleDetailModal } from './VehicleDetailModal';
import * as vehicleDetailApi from '../api/vehicleDetail';
import type { VehicleDetail } from '../types';

vi.mock('../api/vehicleDetail');

const mockedGetVehicleDetail = vi.mocked(vehicleDetailApi.getVehicleDetail);

const detail: VehicleDetail = {
  id: '1',
  make: 'Škoda',
  model: 'Octavia',
  trim: 'Selection',
  price: { amount: 700000, currency: 'CZK' },
  score: null,
  specs: ['Diesel'],
  flag: null,
  powertrain: {
    fuelType: 'diesel',
    transmission: 'Automatická',
    drivetrain: 'fwd',
    powerKw: 110,
    powerHp: 150,
    consumptionMin: 4.5,
    consumptionMax: 5.1,
    consumptionUnit: 'l_100km',
    co2MinGKm: 118,
    co2MaxGKm: 130,
  },
  colors: [{ name: 'Modrá Racing', finishType: 'metallic', surcharge: { amount: 15000, currency: 'CZK' } }],
  standardEquipment: ['Klimatizace', 'Tempomat'],
  optionalEquipment: [
    { name: 'Tažné zařízení', category: 'equipment', surcharge: { amount: 12000, currency: 'CZK' } },
  ],
  priceHistory: [
    {
      validFrom: '2026-01-01',
      validTo: null,
      price: { amount: 700000, currency: 'CZK' },
      lowestPrice30d: { amount: 690000, currency: 'CZK' },
    },
  ],
};

beforeEach(() => {
  vi.resetAllMocks();
});

describe('VehicleDetailModal', () => {
  it('shows a loading state, then the vehicle detail', async () => {
    mockedGetVehicleDetail.mockResolvedValue(detail);
    render(<VehicleDetailModal configurationId="1" onClose={vi.fn()} />);

    expect(screen.getByText(/načítám detail vozu/i)).toBeInTheDocument();

    expect(await screen.findByText('Škoda Octavia Selection')).toBeInTheDocument();
    expect(screen.getByText('Nafta')).toBeInTheDocument();
    expect(screen.getByText(/Modrá Racing/)).toBeInTheDocument();
    expect(screen.getByText('Klimatizace')).toBeInTheDocument();
    expect(screen.getByText(/Tažné zařízení/)).toBeInTheDocument();
    expect(mockedGetVehicleDetail).toHaveBeenCalledWith('1');
  });

  it('shows an error state when the fetch fails', async () => {
    mockedGetVehicleDetail.mockRejectedValue(new Error('boom'));
    render(<VehicleDetailModal configurationId="1" onClose={vi.fn()} />);

    expect(await screen.findByText(/nepodařilo se načíst detail vozu/i)).toBeInTheDocument();
  });

  it('calls onClose when the close button is clicked', async () => {
    mockedGetVehicleDetail.mockResolvedValue(detail);
    const onClose = vi.fn();
    render(<VehicleDetailModal configurationId="1" onClose={onClose} />);
    await screen.findByText('Škoda Octavia Selection');

    await userEvent.click(screen.getByRole('button', { name: 'Zavřít' }));
    expect(onClose).toHaveBeenCalled();
  });

  it('calls onClose when the backdrop is clicked', async () => {
    mockedGetVehicleDetail.mockResolvedValue(detail);
    const onClose = vi.fn();
    const { container } = render(<VehicleDetailModal configurationId="1" onClose={onClose} />);
    await screen.findByText('Škoda Octavia Selection');

    const backdrop = container.querySelector('.bg-black\\/40');
    expect(backdrop).not.toBeNull();
    await userEvent.click(backdrop as Element);
    expect(onClose).toHaveBeenCalled();
  });

  it('calls onClose when Escape is pressed', async () => {
    mockedGetVehicleDetail.mockResolvedValue(detail);
    const onClose = vi.fn();
    render(<VehicleDetailModal configurationId="1" onClose={onClose} />);
    await screen.findByText('Škoda Octavia Selection');

    await userEvent.keyboard('{Escape}');
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });
});
