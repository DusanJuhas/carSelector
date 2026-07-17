import { useEffect, useRef } from 'react';
import type { ChatMessage } from '../types';
import { ChatMessageBubble } from './ChatMessageBubble';

export interface ChatColumnProps {
  messages: ChatMessage[];
  nextSuggestion: string | null;
  onSelectSuggestion: () => void;
}

export function ChatColumn({ messages, nextSuggestion, onSelectSuggestion }: ChatColumnProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  return (
    <div className="flex w-[400px] shrink-0 flex-col border-r border-border">
      <div ref={scrollRef} className="flex min-h-0 flex-1 flex-col gap-3.5 overflow-y-auto p-5">
        {messages.map((message, i) => (
          <ChatMessageBubble key={i} message={message} />
        ))}
      </div>
      <div className="flex flex-col gap-2.5 border-t border-border p-4 px-5">
        {nextSuggestion ? (
          <button
            type="button"
            onClick={onSelectSuggestion}
            className="rounded-control border border-accent bg-accent-soft px-3.5 py-2.5 text-left text-[13px] leading-relaxed text-text"
          >
            {nextSuggestion}
          </button>
        ) : (
          <div className="py-1.5 text-center text-[12.5px] text-subtext">
            Conversation complete — shortlist finalized.
          </div>
        )}
        <div className="rounded-full border border-border bg-ai-bubble px-4 py-2.5 text-[13px] text-subtext">
          Type your reply…
        </div>
      </div>
    </div>
  );
}
