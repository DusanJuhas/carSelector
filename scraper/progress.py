"""Machine-readable progress lines for whoever runs the scraper as a
subprocess - the backend's admin console (`backend/app/ui/admin.py`) turns
them into a progress bar and keeps them out of the visible log.

One line per update, on stdout:

    PROGRESS {"step": 7, "steps": 20, "item": "skoda", "sub": 3, "subs": 12}

`step` (1-based) of `steps` is the outer unit (a source), `item` names it,
and the optional `sub`/`subs` (0-based count done / total) is progress
inside it (documents of that source). A terminal run ignores these lines
like any other output.
"""

from __future__ import annotations

import json

PREFIX = "PROGRESS "


def report_progress(step: int, steps: int, item: str, sub: int | None = None, subs: int | None = None) -> None:
    """Prints one progress line, flushed immediately so a piped reader
    sees it now rather than when the output buffer fills.

    Args:
        step: 1-based index of the current outer unit.
        steps: Total number of outer units.
        item: Name of the current outer unit (e.g. a parser key).
        sub: How many inner units of `step` are done, if known.
        subs: Total inner units of `step`, if known.
    """
    payload: dict[str, object] = {"step": step, "steps": steps, "item": item}
    if sub is not None and subs is not None:
        payload["sub"] = sub
        payload["subs"] = subs
    print(PREFIX + json.dumps(payload, ensure_ascii=False), flush=True)
