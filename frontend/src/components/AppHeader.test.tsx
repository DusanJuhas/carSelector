import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { AppHeader } from './AppHeader';

describe('AppHeader', () => {
  it('renders the requirements count badge', () => {
    render(<AppHeader requirementsCount={4} onRestart={vi.fn()} onToggleDrawer={vi.fn()} />);
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('calls onRestart and onToggleDrawer on click', async () => {
    const onRestart = vi.fn();
    const onToggleDrawer = vi.fn();
    render(<AppHeader requirementsCount={0} onRestart={onRestart} onToggleDrawer={onToggleDrawer} />);

    await userEvent.click(screen.getByRole('button', { name: 'Restart' }));
    expect(onRestart).toHaveBeenCalledOnce();

    await userEvent.click(screen.getByRole('button', { name: /technical requirements/i }));
    expect(onToggleDrawer).toHaveBeenCalledOnce();
  });
});
