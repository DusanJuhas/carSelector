import type { Car } from './car';
import type { UserRequirement } from './requirement';

export type ChatRole = 'user' | 'assistant';

export interface ChatMessage {
  role: ChatRole;
  text: string;
}

export interface ConversationTurn {
  userText: string;
  assistantText: string;
  stageName: string;
  requirements: UserRequirement[];
  cars: Car[];
}
