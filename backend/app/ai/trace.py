"""In-memory trace of every LLM API exchange, for the admin console's "AI
komunikace" tab (`app/ui/admin.py`).

`AnthropicLlmClient` / `GroqLlmClient` (`app/ai/llm.py`) record one
`LlmTraceEntry` per `complete()` call: the exact request payload handed to
the SDK, the full raw response (or the error and its body), the extracted
reply text, token usage and latency. The API key is never part of it - it
lives on the SDK client, not in the request payload.

Kept in process memory only, in a bounded ring buffer
(`LLM_TRACE_MAX_ENTRIES`, oldest dropped first; `0` turns tracing off):
the payloads contain users' own chat text, so nothing is written to disk,
and a restart clears it - same lifetime as the runtime API key in
`app/ai/client.py`. Per process: with several workers, each has its own.
"""

import json
import threading
from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime
from itertools import count
from typing import Any

from app.core import config

# What the current LLM call is for (e.g. "requirement_extraction"), set by
# the caller around `complete()` via `llm_purpose()`. A contextvar rather
# than a `complete()` argument so `LlmClient`'s signature - and every test
# fake implementing it - stays unchanged.
_purpose: ContextVar[str | None] = ContextVar("llm_purpose", default=None)


@contextmanager
def llm_purpose(purpose: str) -> Iterator[None]:
    """Labels every LLM call made inside the `with` block with `purpose`
    in the trace.

    Args:
        purpose: Short machine-readable label, e.g. `"explanation"` - the
            admin console translates it via `admin.trace.purposes.*`.
    """
    token = _purpose.set(purpose)
    try:
        yield
    finally:
        _purpose.reset(token)


def to_jsonable(value: Any) -> Any:
    """Best-effort conversion of an SDK object (a pydantic model in both
    SDKs) into plain JSON-serializable data for display.

    Args:
        value: Response object, error body, or anything else.

    Returns:
        `value.model_dump(mode="json")` for pydantic models, `value` itself
        if it already serializes as JSON, otherwise its `repr()`.
    """
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump(mode="json")
        except Exception:  # noqa: BLE001 - display only, never fail the call
            pass
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


@dataclass(frozen=True)
class LlmTraceEntry:
    """One request/response exchange with an LLM provider.

    Attributes:
        id: Sequence number, unique within this process.
        started_at: When the request was sent (local time, tz-aware).
        provider: `"groq"` or `"anthropic"`.
        model: Model id sent with the request.
        purpose: What the call was for (see `llm_purpose`), `None` if the
            caller didn't say.
        request: The exact keyword arguments passed to the SDK's create call.
        response: The full raw response as JSON data, or the error body
            from the provider if the call failed (may be `None`).
        reply_text: The text `complete()` returned; `None` on failure.
        duration_ms: Wall-clock time of the SDK call.
        input_tokens: Prompt tokens billed, if the provider reported usage.
        output_tokens: Completion tokens billed (incl. reasoning), likewise.
        error_code: `AiProviderError` code (`ai_rate_limited`, ...), or
            `"exception"` for an unexpected exception; `None` on success.
        error_message: The error's text; `None` on success.
    """

    id: int
    started_at: datetime
    provider: str
    model: str
    purpose: str | None
    request: dict[str, Any]
    response: Any
    reply_text: str | None
    duration_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    error_code: str | None = None
    error_message: str | None = None

    @property
    def ok(self) -> bool:
        """True if the call returned a reply."""
        return self.error_code is None


class LlmTraceLog:
    """Thread-safe bounded log of `LlmTraceEntry`s. Written from the
    worker threads `nicegui.run.io_bound` runs AI calls in, read from the
    admin page's event loop - hence the lock.
    """

    def __init__(self, max_entries: int) -> None:
        """Args:
        max_entries: How many entries to keep; older ones are dropped.
            `0` (or less) disables recording entirely.
        """
        self._max_entries = max(max_entries, 0)
        self._entries: deque[LlmTraceEntry] = deque(maxlen=self._max_entries or None)
        self._lock = threading.Lock()
        self._ids = count(1)
        self._version = 0

    @property
    def enabled(self) -> bool:
        """Whether `record()` keeps anything."""
        return self._max_entries > 0

    @property
    def max_entries(self) -> int:
        """Configured capacity."""
        return self._max_entries

    @property
    def version(self) -> int:
        """Increments on every change - lets a viewer poll cheaply for
        "anything new since I last rendered?"."""
        return self._version

    def record(
        self,
        *,
        started_at: datetime,
        provider: str,
        model: str,
        request: dict[str, Any],
        response: Any,
        reply_text: str | None,
        duration_ms: float,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> LlmTraceEntry | None:
        """Appends one exchange; the purpose is taken from the current
        `llm_purpose()` context. See `LlmTraceEntry` for the arguments.

        Returns:
            The stored entry, or `None` if tracing is disabled.
        """
        if not self.enabled:
            return None
        with self._lock:
            entry = LlmTraceEntry(
                id=next(self._ids),
                started_at=started_at,
                provider=provider,
                model=model,
                purpose=_purpose.get(),
                request=request,
                response=to_jsonable(response),
                reply_text=reply_text,
                duration_ms=duration_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                error_code=error_code,
                error_message=error_message,
            )
            self._entries.append(entry)
            self._version += 1
            return entry

    def entries(self) -> list[LlmTraceEntry]:
        """All kept entries, newest first."""
        with self._lock:
            return list(reversed(self._entries))

    def clear(self) -> None:
        """Drops every entry (ids keep counting up)."""
        with self._lock:
            self._entries.clear()
            self._version += 1


trace_log = LlmTraceLog(config.LLM_TRACE_MAX_ENTRIES)
