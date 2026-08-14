"""Detection of a blocked event loop.

Plombery runs tasks on the event loop when they are coroutines, and in a thread
when they are not. A coroutine that calls blocking code — `time.sleep`,
`requests.get`, a long CPU loop — holds the loop for its whole duration, and
while it does nothing else in the process runs: the API stops answering, the
websocket stops streaming and the scheduler stops firing.

The symptom is a frozen UI, and nothing in the stack points at the cause. This
watchdog measures how late the loop is and names the task holding it.
"""

import asyncio
import time
from typing import Optional

from contextlib import contextmanager
from typing import Dict, Iterator

from plombery._internals.logging import logger


# How often the loop is probed
_PROBE_INTERVAL = 0.25

_watchdog_task: Optional[asyncio.Task] = None

# The tasks currently executing, by task run ID.
#
# A contextvar would not do: the watchdog runs in an asyncio task of its own,
# which carries the context it was created with and never sees the one the
# executor sets. The loop is single threaded, so a plain dict is safe.
_running_tasks: Dict[str, str] = {}

# Tasks that ran at any point since the last probe.
#
# A task that both starts and finishes while the loop is blocked is gone from
# `_running_tasks` by the time the watchdog wakes up, which is precisely the
# case worth reporting, so it is remembered until the next probe clears it.
_recent_tasks: Dict[str, str] = {}


@contextmanager
def track_running_task(task_run_id: str, task_id: str) -> Iterator[None]:
    """Record a task as running, so the watchdog can name it if it blocks."""

    _running_tasks[task_run_id] = task_id
    _recent_tasks[task_run_id] = task_id

    try:
        yield
    finally:
        _running_tasks.pop(task_run_id, None)


async def _monitor(threshold: float) -> None:
    while True:
        started = time.perf_counter()

        await asyncio.sleep(_PROBE_INTERVAL)

        # However long the sleep actually took beyond what was asked is time
        # the loop spent unable to run anything else.
        lag = time.perf_counter() - started - _PROBE_INTERVAL

        if lag < threshold:
            _recent_tasks.clear()
            continue

        running = sorted(set(_running_tasks.values()) | set(_recent_tasks.values()))
        _recent_tasks.clear()

        if running:
            logger.warning(
                "The event loop was blocked for %.1fs while these tasks were "
                "running: %s. An async task must not call blocking code: use "
                "await, or declare the task with `def` instead of `async def` "
                "so that Plombery runs it in a thread.",
                lag,
                ", ".join(running),
            )
        else:
            logger.warning(
                "The event loop was blocked for %.1fs. Something in this "
                "process is running blocking code without yielding.",
                lag,
            )


def start_watchdog(threshold_seconds: float) -> None:
    """Start watching the loop. Does nothing if the threshold is disabled."""

    global _watchdog_task

    if not threshold_seconds or threshold_seconds <= 0:
        return

    if _watchdog_task and not _watchdog_task.done():
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Not started from within a loop: nothing to watch
        return

    _watchdog_task = loop.create_task(
        _monitor(threshold_seconds), name="plombery:event-loop-watchdog"
    )


def stop_watchdog() -> None:
    global _watchdog_task

    if _watchdog_task and not _watchdog_task.done():
        _watchdog_task.cancel()

    _watchdog_task = None
