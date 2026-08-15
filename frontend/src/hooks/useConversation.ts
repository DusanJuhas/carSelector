import { useCallback, useEffect, useRef, useState } from 'react';
import { useConversationStore } from '../store/conversationStore';
import { ApiError } from '../api/client';
import { sendMessage as apiSendMessage, startConversation as apiStartConversation } from '../api/conversation';
import type { ChatMessage, Car, UserRequirement } from '../types';

/** Coarse error category the UI branches on - see `ChatPage`'s error banner. */
export type ConversationError = 'ai_not_configured' | 'network_error' | 'unknown_error' | null;

export interface UseConversationResult {
  messages: ChatMessage[];
  requirements: UserRequirement[];
  cars: Car[];
  /** True once the recommendation engine has run at least once - see `conversationStore`. */
  hasNarrowed: boolean;
  /** True only while the very first `startConversation` call is in flight. */
  isLoading: boolean;
  /** True while a `sendMessage` call is in flight. */
  isSending: boolean;
  error: ConversationError;
  /** Sends `text` as the user's next message. No-ops if already sending, or before the conversation has started. */
  send: (text: string) => void;
  /** Abandons the current conversation and starts a fresh one. */
  restart: () => void;
  drawerOpen: boolean;
  toggleDrawer: () => void;
  closeDrawer: () => void;
}

/**
 * Orchestrates the chat flow against the real backend: starts a
 * conversation on mount, and exposes `send`/`restart` that call the API
 * (`api/conversation.ts`) and write the result into `conversationStore`.
 *
 * @returns The current conversation state plus the actions to drive it -
 *   see `ChatPage` for how this is consumed.
 */
export function useConversation(): UseConversationResult {
  const conversationId = useConversationStore((state) => state.conversationId);
  const messages = useConversationStore((state) => state.messages);
  const requirements = useConversationStore((state) => state.requirements);
  const cars = useConversationStore((state) => state.cars);
  const hasNarrowed = useConversationStore((state) => state.hasNarrowed);
  const drawerOpen = useConversationStore((state) => state.drawerOpen);
  const setConversation = useConversationStore((state) => state.setConversation);
  const appendMessage = useConversationStore((state) => state.appendMessage);
  const setResult = useConversationStore((state) => state.setResult);
  const reset = useConversationStore((state) => state.reset);
  const toggleDrawer = useConversationStore((state) => state.toggleDrawer);
  const closeDrawer = useConversationStore((state) => state.closeDrawer);

  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<ConversationError>(null);

  const begin = useCallback(() => {
    setIsLoading(true);
    setError(null);
    apiStartConversation()
      .then(({ conversationId: newConversationId, introMessage }) =>
        setConversation(newConversationId, introMessage),
      )
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? (err.code as ConversationError) : 'unknown_error');
      })
      .finally(() => setIsLoading(false));
  }, [setConversation]);

  // Starts the conversation once on mount. Guarded with a ref (not just
  // an empty dep array) because StrictMode's dev-only double-invoke would
  // otherwise fire this twice, opening two conversations server-side and
  // silently discarding the first's id.
  const hasStarted = useRef(false);
  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;
    begin();
  }, [begin]);

  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!conversationId || !trimmed || isSending) return;

      appendMessage({ role: 'user', text: trimmed });
      setIsSending(true);
      setError(null);
      apiSendMessage(conversationId, trimmed)
        .then(({ assistantMessage, requirements: newRequirements, cars: newCars, searched }) => {
          appendMessage(assistantMessage);
          setResult(newRequirements, newCars, searched);
        })
        .catch((err: unknown) => {
          setError(err instanceof ApiError ? (err.code as ConversationError) : 'unknown_error');
        })
        .finally(() => setIsSending(false));
    },
    [conversationId, isSending, appendMessage, setResult],
  );

  const restart = useCallback(() => {
    reset();
    hasStarted.current = false;
    begin();
  }, [reset, begin]);

  return {
    messages,
    requirements,
    cars,
    hasNarrowed,
    isLoading,
    isSending,
    error,
    send,
    restart,
    drawerOpen,
    toggleDrawer,
    closeDrawer,
  };
}
