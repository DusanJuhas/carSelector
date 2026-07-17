import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ChatMessageBubble } from './ChatMessageBubble';

describe('ChatMessageBubble', () => {
  it('renders the message text', () => {
    render(<ChatMessageBubble message={{ role: 'assistant', text: 'Hi there' }} />);
    expect(screen.getByText('Hi there')).toBeInTheDocument();
  });
});
