import type { ChatMessage } from '../types';

export interface ChatMessageBubbleProps {
  message: ChatMessage;
}

export function ChatMessageBubble({ message }: ChatMessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[82%] rounded-control border px-3.5 py-2.5 text-[13.5px] leading-relaxed ${
          isUser
            ? 'border-accent bg-accent text-accent-text'
            : 'border-border bg-ai-bubble text-text'
        }`}
      >
        {message.text}
      </div>
    </div>
  );
}
