import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it } from 'vitest';
import { ChatPage } from './ChatPage';
import { useConversationStore } from '../store/conversationStore';

afterEach(() => {
  useConversationStore.setState({ turnIndex: 0, drawerOpen: false });
});

describe('ChatPage', () => {
  it('shows the empty shortlist state before the conversation starts', () => {
    render(<ChatPage />);
    expect(screen.getByText('Váš výběr')).toBeInTheDocument();
    expect(screen.getByText(/začněte konverzaci/i)).toBeInTheDocument();
  });

  it('reveals requirements and a ranked shortlist after picking a suggested reply', async () => {
    render(<ChatPage />);

    await userEvent.click(screen.getByText(/čtyřčlenná rodina/i));

    expect(screen.getByText(/\d+ shod/i)).toBeInTheDocument();
    expect(screen.getByText('Subaru Outback Wilderness')).toBeInTheDocument();
  });

  it('restarts the conversation back to the empty state', async () => {
    render(<ChatPage />);

    await userEvent.click(screen.getByText(/čtyřčlenná rodina/i));
    await userEvent.click(screen.getByRole('button', { name: 'Restartovat' }));

    expect(screen.getByText('Váš výběr')).toBeInTheDocument();
  });
});
