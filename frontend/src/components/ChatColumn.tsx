import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { ChatMessage } from '../types';
import { ChatMessageBubble } from './ChatMessageBubble';

export interface ChatColumnProps {
  messages: ChatMessage[];
  /** True while waiting on the assistant's reply - disables the input and shows a typing indicator. */
  isSending: boolean;
  onSend: (text: string) => void;
}

export function ChatColumn({ messages, isSending, onSend }: ChatColumnProps) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, isSending]);

  const submit = () => {
    const text = draft.trim();
    if (!text || isSending) return;
    onSend(text);
    setDraft('');
  };

  return (
    <div className="flex w-[400px] shrink-0 flex-col border-r border-border">
      <div ref={scrollRef} className="flex min-h-0 flex-1 flex-col gap-3.5 overflow-y-auto p-5">
        {messages.map((message, i) => (
          <ChatMessageBubble key={i} message={message} />
        ))}
        {isSending && (
          <div className="flex justify-start">
            <div className="max-w-[82%] rounded-control border border-border bg-ai-bubble px-3.5 py-2.5 text-[13.5px] italic text-subtext">
              {t('chat.sending')}
            </div>
          </div>
        )}
      </div>
      <form
        className="flex gap-2 border-t border-border p-4 px-5"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <input
          type="text"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          disabled={isSending}
          placeholder={t('chat.typePlaceholder')}
          className="min-w-0 flex-1 rounded-full border border-border bg-ai-bubble px-4 py-2.5 text-[13px] text-text placeholder:text-subtext focus:border-accent focus:outline-none disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={isSending || !draft.trim()}
          className="shrink-0 rounded-full bg-accent px-4 py-2.5 text-[13px] font-semibold text-accent-text disabled:opacity-50"
        >
          {t('chat.send')}
        </button>
      </form>
    </div>
  );
}
