import { create } from 'zustand';
import { CONVERSATION_SCRIPT } from '../api/mock/conversation';

interface ConversationState {
  turnIndex: number;
  drawerOpen: boolean;
  advance: () => void;
  restart: () => void;
  toggleDrawer: () => void;
  closeDrawer: () => void;
}

export const useConversationStore = create<ConversationState>((set) => ({
  turnIndex: 0,
  drawerOpen: false,
  advance: () =>
    set((state) => ({
      turnIndex: Math.min(state.turnIndex + 1, CONVERSATION_SCRIPT.length),
    })),
  restart: () => set({ turnIndex: 0, drawerOpen: false }),
  toggleDrawer: () => set((state) => ({ drawerOpen: !state.drawerOpen })),
  closeDrawer: () => set({ drawerOpen: false }),
}));
