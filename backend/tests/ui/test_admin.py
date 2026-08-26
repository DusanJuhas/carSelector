"""Covers app/ui/admin.py's JobState - the generic subprocess-streaming
mechanism both admin buttons share. Doesn't invoke the real scraper/import
scripts (network calls, minutes of runtime) - a trivial subprocess
exercises the same streaming/completion code path.
"""

import sys

from app.ui.admin import JobState


async def test_job_state_streams_output_and_completes() -> None:
    state = JobState()
    refresh_calls = 0

    def on_output() -> None:
        nonlocal refresh_calls
        refresh_calls += 1

    await state.run([sys.executable, "-c", "print('line one'); print('line two')"], on_output)

    assert state.lines == ["line one", "line two"]
    assert state.return_code == 0
    assert state.is_running is False
    assert refresh_calls >= 3  # start + >=1 per line + completion


async def test_job_state_captures_nonzero_exit_code() -> None:
    state = JobState()
    await state.run([sys.executable, "-c", "import sys; sys.exit(2)"], lambda: None)
    assert state.return_code == 2
    assert state.is_running is False


async def test_job_state_is_a_noop_while_already_running() -> None:
    state = JobState()
    state.is_running = True
    await state.run([sys.executable, "-c", "print('should not run')"], lambda: None)
    assert state.lines == []
