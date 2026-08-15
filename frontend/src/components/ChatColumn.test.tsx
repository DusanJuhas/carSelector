import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ChatColumn } from './ChatColumn';

describe('ChatColumn', () => {
  it('calls onSelectSuggestion when the suggested reply chip is clicked', async () => {
    const onSelectSuggestion = vi.fn();
    render(
      <ChatColumn
        messages={[{ role: 'assistant', text: 'Ahoj!' }]}
        nextSuggestion="Hodně jezdíme v horách"
        onSelectSuggestion={onSelectSuggestion}
      />,
    );

    await userEvent.click(screen.getByText('Hodně jezdíme v horách'));
    expect(onSelectSuggestion).toHaveBeenCalledOnce();
  });

  it('shows a completion message when there is no next suggestion', () => {
    render(
      <ChatColumn messages={[{ role: 'assistant', text: 'Ahoj!' }]} nextSuggestion={null} onSelectSuggestion={vi.fn()} />,
    );
    expect(screen.getByText(/konverzace dokončena/i)).toBeInTheDocument();
  });
});
