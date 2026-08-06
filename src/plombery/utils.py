import asyncio
from datetime import datetime, timezone
from typing import Coroutine, List

from plombery._internals.logging import logger


# Keeps a strong reference to the running tasks: `asyncio.create_task` only
# holds a weak one, so without this the garbage collector is free to destroy a
# task while it's still running.
_background_tasks = set()


def run_all_coroutines(coroutines: List[Coroutine]):
    """
    Run all coroutines in parallel without blocking
    """

    def _on_task_done(future: asyncio.Task):
        _background_tasks.discard(future)

        # `future.exception()` raises CancelledError instead of returning it,
        # so a cancelled task has to be handled before asking for the exception.
        if future.cancelled():
            return

        if exc := future.exception():
            logger.error("One coroutine failed", exc_info=exc)

    for coroutine in coroutines:
        task = asyncio.create_task(coroutine)

        _background_tasks.add(task)
        task.add_done_callback(_on_task_done)


def utcnow():
    return datetime.now(tz=timezone.utc)
