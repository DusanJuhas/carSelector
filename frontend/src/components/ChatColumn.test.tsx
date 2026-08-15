import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ChatColumn } from './ChatColumn';

describe('ChatColumn', () => {
  it('sends the typed message and clears the input', async () => {
    const onSend = vi.fn();
    render(
      <ChatColumn messages={[{ role: 'assistant', text: 'Ahoj!' }]} isSending={false} onSend={onSend} />,
    );

    const input = screen.getByPlaceholderText('Napište odpověď…');
    await userEvent.type(input, 'Hodně jezdíme v horách');
    await userEvent.click(screen.getByRole('button', { name: 'Odeslat' }));

    expect(onSend).toHaveBeenCalledWith('Hodně jezdíme v horách');
    expect(input).toHaveValue('');
  });

  it('sends on Enter as well as on the button click', async () => {
    const onSend = vi.fn();
    render(<ChatColumn messages={[]} isSending={false} onSend={onSend} />);

    await userEvent.type(screen.getByPlaceholderText('Napište odpověď…'), 'Rodinné auto{Enter}');

    expect(onSend).toHaveBeenCalledWith('Rodinné auto');
  });

  it('does not send an empty or whitespace-only message', async () => {
    const onSend = vi.fn();
    render(<ChatColumn messages={[]} isSending={false} onSend={onSend} />);

    await userEvent.type(screen.getByPlaceholderText('Napište odpověď…'), '   {Enter}');

    expect(onSend).not.toHaveBeenCalled();
  });

  it('disables the input and shows a typing indicator while sending', () => {
    render(<ChatColumn messages={[]} isSending={true} onSend={vi.fn()} />);

    expect(screen.getByPlaceholderText('Napište odpověď…')).toBeDisabled();
    expect(screen.getByText('Přemýšlím…')).toBeInTheDocument();
  });
});
