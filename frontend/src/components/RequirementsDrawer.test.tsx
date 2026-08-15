import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { RequirementsDrawer } from './RequirementsDrawer';
import type { UserRequirement } from '../types';

const requirements: UserRequirement[] = [
  { label: 'Pohon', value: '4×4', source: '„kluzké silnice“', changed: true },
];

describe('RequirementsDrawer', () => {
  it('shows an empty-state message when there are no requirements', () => {
    render(<RequirementsDrawer requirements={[]} open onClose={vi.fn()} />);
    expect(screen.getByText(/zatím nebyly zachyceny žádné požadavky/i)).toBeInTheDocument();
  });

  it('renders requirement label, value and source', () => {
    render(<RequirementsDrawer requirements={requirements} open onClose={vi.fn()} />);
    expect(screen.getByText('Pohon')).toBeInTheDocument();
    expect(screen.getByText('4×4')).toBeInTheDocument();
    expect(screen.getByText('„kluzké silnice“')).toBeInTheDocument();
  });
});
