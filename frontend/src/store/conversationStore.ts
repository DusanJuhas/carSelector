import { create } from 'zustand';
import type { Car, ChatMessage, UserRequirement } from '../types';

/**
 * Holds the shape of the current conversation - pure state (setters
 * only), no API calls here. Side effects (starting a conversation,
 * sending a message) live in `hooks/useConversation.ts`, per
 * doc/prompt/CLAUDE.md's convention ("side effects only in /src/api or
 * custom hooks").
 */
interface ConversationState {
  conversationId: string | null;
  messages: ChatMessage[];
  requirements: UserRequirement[];
  cars: Car[];
  /**
   * True once the recommendation engine has actually run at least once
   * (backend's `searched` field - see doc/api-contract.md). Distinguishes
   * "AI hasn't narrowed anything yet" (show the full catalog - see
   * `useCatalog`) from "AI searched and found nothing" (`cars` is empty
   * either way, but only the second should say "0 matches").
   */
  hasNarrowed: boolean;
  drawerOpen: boolean;
  /** Sets the just-started conversation's id and appends its opening message. */
  setConversation: (conversationId: string, introMessage: ChatMessage) => void;
  /** Appends one message (user or assistant) to the transcript. */
  appendMessage: (message: ChatMessage) => void;
  /** Replaces the requirements snapshot and shortlist after a turn resolves. */
  setResult: (requirements: UserRequirement[], cars: Car[], searched: boolean) => void;
  /** Clears everything back to the pre-conversation state (for `restart`). */
  reset: () => void;
  toggleDrawer: () => void;
  closeDrawer: () => void;
}

const initialState = {
  conversationId: null as string | null,
  messages: [] as ChatMessage[],
  requirements: [] as UserRequirement[],
  cars: [] as Car[],
  hasNarrowed: false,
  drawerOpen: false,
};

export const useConversationStore = create<ConversationState>((set) => ({
  ...initialState,
  setConversation: (conversationId, introMessage) =>
    set({ conversationId, messages: [introMessage] }),
  appendMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setResult: (requirements, cars, searched) =>
    set((state) => ({ requirements, cars, hasNarrowed: state.hasNarrowed || searched })),
  reset: () => set({ ...initialState }),
  toggleDrawer: () => set((state) => ({ drawerOpen: !state.drawerOpen })),
  closeDrawer: () => set({ drawerOpen: false }),
}));
