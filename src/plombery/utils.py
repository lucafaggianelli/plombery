import asyncio
from typing import Coroutine, List


def run_all_coroutines(coroutines: List[Coroutine]):
    """
    Run all coroutines in parallel without blocking
    """

    tasks = set()

    for coroutine in coroutines:
        task = asyncio.create_task(coroutine)

        tasks.add(task)
        task.add_done_callback(tasks.discard)
