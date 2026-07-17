import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ChatColumn } from './ChatColumn';

describe('ChatColumn', () => {
  it('calls onSelectSuggestion when the suggested reply chip is clicked', async () => {
    const onSelectSuggestion = vi.fn();
    render(
      <ChatColumn
        messages={[{ role: 'assistant', text: 'Hi!' }]}
        nextSuggestion="We drive a lot in the mountains"
        onSelectSuggestion={onSelectSuggestion}
      />,
    );

    await userEvent.click(screen.getByText('We drive a lot in the mountains'));
    expect(onSelectSuggestion).toHaveBeenCalledOnce();
  });

  it('shows a completion message when there is no next suggestion', () => {
    render(
      <ChatColumn messages={[{ role: 'assistant', text: 'Hi!' }]} nextSuggestion={null} onSelectSuggestion={vi.fn()} />,
    );
    expect(screen.getByText(/conversation complete/i)).toBeInTheDocument();
  });
});
