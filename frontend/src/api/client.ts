import axios from 'axios';

/**
 * Base URL for the DriveWise AI backend. Override with VITE_API_BASE_URL
 * (see Vite's env file docs) once there's a deployed backend to point at;
 * defaults to the local dev server (`uvicorn app.main:app --reload`, see
 * backend/README.md).
 */
const baseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';

export const apiClient = axios.create({ baseURL });

/** Shape of doc/api-contract.md's error envelope: `{ error: { code, message, details } }`. */
export interface ApiErrorPayload {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}

/**
 * Thrown by every function in api/ instead of a raw AxiosError, so
 * callers (hooks) can branch on a stable `code` without knowing anything
 * about HTTP status codes or the axios error shape.
 */
export class ApiError extends Error {
  readonly code: string;

  /**
   * @param code - Backend error code (e.g. `"ai_not_configured"`,
   *   `"conversation_not_found"`), or `"network_error"` if the request
   *   never reached the backend at all (no response to read a code from).
   * @param message - Human-readable message, from the backend when
   *   available.
   */
  constructor(code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
  }
}

/**
 * Normalizes anything axios can throw into an `ApiError`.
 *
 * @param error - Value caught from an axios call (typed `unknown` since
 *   that's what a `catch` clause gives you).
 * @returns An `ApiError` with the backend's own `code`/`message` when the
 *   backend responded with doc/api-contract.md's error shape; `"network_error"`
 *   when the request didn't get a response at all (backend down, CORS
 *   rejected, offline); `"unknown_error"` for anything else.
 */
export function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const payload = error.response?.data as ApiErrorPayload | undefined;
    if (payload?.error?.code) {
      return new ApiError(payload.error.code, payload.error.message);
    }
    if (!error.response) {
      return new ApiError('network_error', error.message);
    }
  }
  return new ApiError('unknown_error', error instanceof Error ? error.message : String(error));
}
