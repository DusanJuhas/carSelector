import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ChatPage } from './ChatPage';
import { ApiError } from '../api/client';
import * as conversationApi from '../api/conversation';
import * as catalogApi from '../api/catalog';
import * as vehicleDetailApi from '../api/vehicleDetail';
import { useConversationStore } from '../store/conversationStore';
import { useCatalogStore } from '../store/catalogStore';
import type { Car } from '../types';

vi.mock('../api/conversation');
vi.mock('../api/catalog');
vi.mock('../api/vehicleDetail');

const mockedStart = vi.mocked(conversationApi.startConversation);
const mockedSend = vi.mocked(conversationApi.sendMessage);
const mockedListVehicles = vi.mocked(catalogApi.listVehicles);
const mockedGetVehicleDetail = vi.mocked(vehicleDetailApi.getVehicleDetail);

const octavia: Car = {
  id: '1',
  make: 'Škoda',
  model: 'Octavia',
  trim: 'Selection',
  price: { amount: 700000, currency: 'CZK' },
  score: null,
  specs: ['Diesel'],
  flag: null,
};

const fabia: Car = {
  id: '2',
  make: 'Škoda',
  model: 'Fabia',
  trim: 'Classic',
  price: { amount: 450000, currency: 'CZK' },
  score: null,
  specs: ['Petrol'],
  flag: null,
};

beforeEach(() => {
  vi.resetAllMocks();
  window.localStorage.clear();
  useConversationStore.setState({
    conversationId: null,
    messages: [],
    requirements: [],
    cars: [],
    hasNarrowed: false,
    drawerOpen: false,
  });
  useCatalogStore.setState({ cars: [], page: 0, pageSize: 20, total: 0 });
  mockedStart.mockResolvedValue({
    conversationId: 'conv-1',
    introMessage: { role: 'assistant', text: 'Ahoj! Jak vám mohu pomoci?' },
  });
  mockedListVehicles.mockResolvedValue({ cars: [octavia, fabia], page: 1, pageSize: 20, total: 2 });
});

describe('ChatPage', () => {
  it('shows the full catalog by default, before any discussion narrows it', async () => {
    render(<ChatPage />);

    expect(await screen.findByText('Škoda Octavia Selection')).toBeInTheDocument();
    expect(screen.getByText('Škoda Fabia Classic')).toBeInTheDocument();
    expect(screen.getByText('2 vozy v katalogu')).toBeInTheDocument();
    expect(screen.getByText(/AI vám katalog zúží/i)).toBeInTheDocument();
    // Catalog cars carry no match score - browsing mode, not a recommendation.
    expect(screen.queryByText(/%$/)).not.toBeInTheDocument();
  });

  it('offers to load more of the catalog when more pages exist', async () => {
    mockedListVehicles.mockResolvedValueOnce({ cars: [octavia], page: 1, pageSize: 1, total: 2 });
    render(<ChatPage />);
    await screen.findByText('Škoda Octavia Selection');

    mockedListVehicles.mockResolvedValueOnce({ cars: [fabia], page: 2, pageSize: 1, total: 2 });
    await userEvent.click(screen.getByRole('button', { name: 'Načíst další' }));

    expect(await screen.findByText('Škoda Fabia Classic')).toBeInTheDocument();
    expect(mockedListVehicles).toHaveBeenCalledWith({ page: 2, pageSize: 1 });
  });

  it('switches to the AI-narrowed shortlist once the assistant actually searches', async () => {
    mockedSend.mockResolvedValue({
      assistantMessage: { role: 'assistant', text: 'Tady je váš výběr.' },
      requirements: [{ label: 'Rozpočet', value: '700 000 Kč', source: '"asi 700 000 Kč"', changed: true }],
      cars: [{ ...octavia, score: 90, topPick: true }],
      searched: true,
    });

    render(<ChatPage />);
    await screen.findByText('Škoda Octavia Selection'); // catalog, before narrowing

    await userEvent.type(screen.getByPlaceholderText('Napište odpověď…'), 'Potřebuju rodinné auto{Enter}');

    expect(await screen.findByText('Tady je váš výběr.')).toBeInTheDocument();
    expect(screen.getByText('90%')).toBeInTheDocument();
    expect(screen.queryByText('Škoda Fabia Classic')).not.toBeInTheDocument();
    expect(screen.getByText('1 shoda pro vás')).toBeInTheDocument();
    expect(mockedSend).toHaveBeenCalledWith('conv-1', 'Potřebuju rodinné auto');
  });

  it('stays on the catalog while the AI is still asking a follow-up question', async () => {
    mockedSend.mockResolvedValue({
      assistantMessage: { role: 'assistant', text: 'Jaký je váš rozpočet?' },
      requirements: [],
      cars: [],
      searched: false,
    });

    render(<ChatPage />);
    await screen.findByText('Škoda Octavia Selection');

    await userEvent.type(screen.getByPlaceholderText('Napište odpověď…'), 'Chci rodinné auto{Enter}');

    expect(await screen.findByText('Jaký je váš rozpočet?')).toBeInTheDocument();
    // Still browsing the full catalog, not a (wrongly) empty "0 matches" state.
    expect(screen.getByText('Škoda Octavia Selection')).toBeInTheDocument();
    expect(screen.getByText('Škoda Fabia Classic')).toBeInTheDocument();
    expect(screen.getByText('2 vozy v katalogu')).toBeInTheDocument();
  });

  it('shows a real "no matches" state (not the catalog) when a search finds nothing', async () => {
    mockedSend.mockResolvedValue({
      assistantMessage: { role: 'assistant', text: 'Nic nevyhovuje.' },
      requirements: [{ label: 'Rozpočet', value: '10 000 Kč', source: '"10 000 Kč"', changed: true }],
      cars: [],
      searched: true,
    });

    render(<ChatPage />);
    await screen.findByText('Škoda Octavia Selection');

    await userEvent.type(screen.getByPlaceholderText('Napište odpověď…'), 'Auto za 10 000 Kč{Enter}');

    expect(await screen.findByText('Nic nevyhovuje.')).toBeInTheDocument();
    expect(screen.getByText('0 shod pro vás')).toBeInTheDocument();
    expect(screen.queryByText('Škoda Octavia Selection')).not.toBeInTheDocument();
  });

  it('shows a specific banner when the AI layer is not configured', async () => {
    mockedSend.mockRejectedValue(new ApiError('ai_not_configured', 'no key set'));

    render(<ChatPage />);
    await screen.findByText('Škoda Octavia Selection');

    await userEvent.type(screen.getByPlaceholderText('Napište odpověď…'), 'Potřebuju rodinné auto{Enter}');

    expect(await screen.findByText(/AI vrstva zatím není nastavená/i)).toBeInTheDocument();
    // Browsing mode never went away - this is exactly the fallback it's for.
    expect(screen.getByText('Škoda Octavia Selection')).toBeInTheDocument();
  });

  it('restarts the conversation back to browsing mode', async () => {
    mockedSend.mockResolvedValue({
      assistantMessage: { role: 'assistant', text: 'Tady je váš výběr.' },
      requirements: [],
      cars: [{ ...octavia, score: 90 }],
      searched: true,
    });
    render(<ChatPage />);
    await screen.findByText('Škoda Octavia Selection');
    await userEvent.type(screen.getByPlaceholderText('Napište odpověď…'), 'Rodinné auto{Enter}');
    await screen.findByText('1 shoda pro vás');

    await userEvent.click(screen.getByRole('button', { name: 'Restartovat' }));

    expect(await screen.findByText('2 vozy v katalogu')).toBeInTheDocument();
    expect(mockedStart).toHaveBeenCalledTimes(2);
  });

  it('opens the vehicle detail modal when a car card is clicked', async () => {
    mockedGetVehicleDetail.mockResolvedValue({
      ...octavia,
      powertrain: {
        fuelType: 'diesel',
        transmission: null,
        drivetrain: 'fwd',
        powerKw: null,
        powerHp: null,
        consumptionMin: null,
        consumptionMax: null,
        consumptionUnit: null,
        co2MinGKm: null,
        co2MaxGKm: null,
      },
      colors: [],
      standardEquipment: [],
      optionalEquipment: [],
      priceHistory: [],
    });

    render(<ChatPage />);
    await screen.findByText('Škoda Octavia Selection');

    await userEvent.click(screen.getAllByRole('button', { name: /Škoda Octavia Selection/i })[0]);

    expect(mockedGetVehicleDetail).toHaveBeenCalledWith('1');
    expect(await screen.findByText('Nafta')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Zavřít' }));
    expect(screen.queryByText('Nafta')).not.toBeInTheDocument();
  });

  it('pushes price sorting to the backend in browsing mode, resetting to page 1', async () => {
    render(<ChatPage />);
    await screen.findByText('Škoda Octavia Selection');
    expect(mockedListVehicles).toHaveBeenCalledTimes(1);

    mockedListVehicles.mockResolvedValueOnce({ cars: [fabia, octavia], page: 1, pageSize: 20, total: 2 });
    await userEvent.selectOptions(screen.getByRole('combobox'), 'Cena: od nejnižší');

    await screen.findByText('2 vozy v katalogu');
    expect(mockedListVehicles).toHaveBeenCalledTimes(2);
    expect(mockedListVehicles).toHaveBeenLastCalledWith(
      expect.objectContaining({ page: 1, sort: 'price_asc' }),
    );
  });

  it('sorts the narrowed shortlist client-side without another backend call', async () => {
    mockedSend.mockResolvedValue({
      assistantMessage: { role: 'assistant', text: 'Tady je váš výběr.' },
      requirements: [],
      cars: [
        { ...octavia, score: 90 }, // 700 000 Kč
        { ...fabia, score: 80 }, // 450 000 Kč
      ],
      searched: true,
    });

    render(<ChatPage />);
    await screen.findByText('Škoda Octavia Selection');
    await userEvent.type(screen.getByPlaceholderText('Napište odpověď…'), 'Rodinné auto{Enter}');
    await screen.findByText('2 shody pro vás');

    const callsBeforeSort = mockedListVehicles.mock.calls.length;
    await userEvent.selectOptions(screen.getByRole('combobox'), 'Cena: od nejnižší');

    const cards = screen.getAllByRole('button', { name: /Škoda/i });
    expect(cards[0]).toHaveAccessibleName(/Fabia/); // cheaper car now first
    expect(mockedListVehicles).toHaveBeenCalledTimes(callsBeforeSort); // no extra fetch
  });

  it('lets the user drag cards into "Moje pořadí" and keeps that order', async () => {
    render(<ChatPage />);
    await screen.findByText('Škoda Octavia Selection');

    await userEvent.selectOptions(screen.getByRole('combobox'), 'Moje pořadí');

    const [firstWrapper, secondWrapper] = screen
      .getAllByRole('button', { name: /Škoda/i })
      .map((btn) => btn.parentElement!);
    expect(firstWrapper).toHaveAttribute('draggable', 'true');

    fireEvent.dragStart(secondWrapper);
    fireEvent.dragOver(firstWrapper);
    fireEvent.drop(firstWrapper);

    const reordered = screen.getAllByRole('button', { name: /Škoda/i });
    expect(reordered[0]).toHaveAccessibleName(/Fabia/);
  });
});
