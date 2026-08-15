import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { SortControl } from './SortControl';

describe('SortControl', () => {
  it('shows every sort option, with the current value selected', () => {
    render(<SortControl value="price_asc" onChange={vi.fn()} />);
    const select = screen.getByRole('combobox') as HTMLSelectElement;
    expect(select.value).toBe('price_asc');
    expect(screen.getByRole('option', { name: 'Doporučeno' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Moje pořadí' })).toBeInTheDocument();
  });

  it('calls onChange with the newly selected option', async () => {
    const onChange = vi.fn();
    render(<SortControl value="recommended" onChange={onChange} />);
    await userEvent.selectOptions(screen.getByRole('combobox'), 'Moje pořadí');
    expect(onChange).toHaveBeenCalledWith('custom');
  });
});
