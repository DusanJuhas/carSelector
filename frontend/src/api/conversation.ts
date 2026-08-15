import { apiClient, toApiError } from './client';
import { toCar } from './vehicleSummary';
import type { Car, ChatMessage, UserRequirement } from '../types';
import type { VehicleSummaryDTO } from './vehicleSummary';

/** Wire shape of `POST /api/conversations`'s response (doc/api-contract.md). */
interface ConversationStartResponseDTO {
  conversation_id: string;
  intro_message: string;
}

/** Wire shape of `POST /api/conversations/{id}/messages`'s response. */
interface MessageResponseDTO {
  assistant_text: string;
  // UserRequirement's fields (label/value/source/changed) already match
  // the frontend type 1:1 - see backend/app/schemas/requirement.py.
  requirements: UserRequirement[];
  vehicles: VehicleSummaryDTO[];
  searched: boolean;
}

/** Result of starting a new conversation - see {@link startConversation}. */
export interface StartConversationResult {
  conversationId: string;
  introMessage: ChatMessage;
}

/**
 * Starts a new conversation. Doesn't call the AI layer (see
 * backend/app/services/conversation.py) - always succeeds as long as the
 * backend is reachable, even without `ANTHROPIC_API_KEY` configured.
 *
 * @returns The new conversation's id (pass to {@link sendMessage}) and
 *   its opening assistant message, ready to render.
 * @throws {ApiError} `"network_error"` if the backend isn't reachable.
 */
export async function startConversation(): Promise<StartConversationResult> {
  try {
    const { data } = await apiClient.post<ConversationStartResponseDTO>('/conversations');
    return {
      conversationId: data.conversation_id,
      introMessage: { role: 'assistant', text: data.intro_message },
    };
  } catch (error) {
    throw toApiError(error);
  }
}

/** Result of sending a message - see {@link sendMessage}. */
export interface SendMessageResult {
  assistantMessage: ChatMessage;
  requirements: UserRequirement[];
  cars: Car[];
  /** True once the recommendation engine actually ran this turn - see doc/api-contract.md's note on this field. False while the AI is still asking follow-up questions. */
  searched: boolean;
}

/**
 * Sends one user message in an existing conversation: extracts/merges
 * requirements, and once there's enough to search on, returns a ranked,
 * AI-explained shortlist.
 *
 * @param conversationId - Id returned by an earlier {@link startConversation} call.
 * @param text - The user's message.
 * @returns The assistant's reply plus the (possibly unchanged)
 *   requirements snapshot and (possibly empty, if still gathering
 *   requirements) shortlist. `searched` distinguishes "still gathering
 *   requirements" (`false`, `cars` always empty) from "searched, found
 *   nothing" (`true`, `cars` empty) - see `ChatPage`'s use of it to fall
 *   back to browsing the full catalog only in the former case.
 * @throws {ApiError} `"conversation_not_found"` if `conversationId` is
 *   stale (e.g. the backend restarted - conversation state isn't
 *   persisted, see backend/app/services/conversation.py);
 *   `"ai_not_configured"` if the backend has no `ANTHROPIC_API_KEY`;
 *   `"network_error"` if the backend isn't reachable.
 */
export async function sendMessage(conversationId: string, text: string): Promise<SendMessageResult> {
  try {
    const { data } = await apiClient.post<MessageResponseDTO>(
      `/conversations/${conversationId}/messages`,
      { text },
    );
    return {
      assistantMessage: { role: 'assistant', text: data.assistant_text },
      requirements: data.requirements,
      cars: data.vehicles.map(toCar),
      searched: data.searched,
    };
  } catch (error) {
    throw toApiError(error);
  }
}
