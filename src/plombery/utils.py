import asyncio
from typing import Coroutine, List


def run_all_coroutines(coroutines: List[Coroutine]):
    """
    Run all coroutines in parallel without blocking
    """

    tasks = set()

    def _on_task_done(future: asyncio.Task):
        if exc := future.exception():
            print("One coroutine failed", exc)
        tasks.discard(future)

    for coroutine in coroutines:
        task = asyncio.create_task(coroutine)

        tasks.add(task)
        task.add_done_callback(_on_task_done)
