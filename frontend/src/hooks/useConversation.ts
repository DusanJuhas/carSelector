import { useMemo } from 'react';
import { useConversationStore } from '../store/conversationStore';
import { CONVERSATION_SCRIPT, INTRO_MESSAGE } from '../api/mock/conversation';
import type { ChatMessage, Car, UserRequirement } from '../types';

export interface UseConversationResult {
  messages: ChatMessage[];
  nextSuggestion: string | null;
  isComplete: boolean;
  requirements: UserRequirement[];
  cars: Car[];
  stageName: string | null;
  advance: () => void;
  restart: () => void;
  drawerOpen: boolean;
  toggleDrawer: () => void;
  closeDrawer: () => void;
}

export function useConversation(): UseConversationResult {
  const turnIndex = useConversationStore((state) => state.turnIndex);
  const drawerOpen = useConversationStore((state) => state.drawerOpen);
  const advance = useConversationStore((state) => state.advance);
  const restart = useConversationStore((state) => state.restart);
  const toggleDrawer = useConversationStore((state) => state.toggleDrawer);
  const closeDrawer = useConversationStore((state) => state.closeDrawer);

  const messages = useMemo<ChatMessage[]>(() => {
    const result: ChatMessage[] = [{ role: 'assistant', text: INTRO_MESSAGE }];
    for (let i = 0; i < turnIndex; i++) {
      result.push({ role: 'user', text: CONVERSATION_SCRIPT[i].userText });
      result.push({ role: 'assistant', text: CONVERSATION_SCRIPT[i].assistantText });
    }
    return result;
  }, [turnIndex]);

  const activeTurn = turnIndex > 0 ? CONVERSATION_SCRIPT[turnIndex - 1] : null;
  const isComplete = turnIndex >= CONVERSATION_SCRIPT.length;

  return {
    messages,
    nextSuggestion: isComplete ? null : CONVERSATION_SCRIPT[turnIndex].userText,
    isComplete,
    requirements: activeTurn?.requirements ?? [],
    cars: activeTurn?.cars ?? [],
    stageName: activeTurn?.stageName ?? null,
    advance,
    restart,
    drawerOpen,
    toggleDrawer,
    closeDrawer,
  };
}
