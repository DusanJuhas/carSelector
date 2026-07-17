import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { RequirementsDrawer } from './RequirementsDrawer';
import type { UserRequirement } from '../types';

const requirements: UserRequirement[] = [
  { label: 'Drivetrain', value: 'AWD', source: '"snowy roads"', changed: true },
];

describe('RequirementsDrawer', () => {
  it('shows an empty-state message when there are no requirements', () => {
    render(<RequirementsDrawer requirements={[]} open onClose={vi.fn()} />);
    expect(screen.getByText(/no requirements captured yet/i)).toBeInTheDocument();
  });

  it('renders requirement label, value and source', () => {
    render(<RequirementsDrawer requirements={requirements} open onClose={vi.fn()} />);
    expect(screen.getByText('Drivetrain')).toBeInTheDocument();
    expect(screen.getByText('AWD')).toBeInTheDocument();
    expect(screen.getByText('"snowy roads"')).toBeInTheDocument();
  });
});
