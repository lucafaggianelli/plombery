from asyncio import iscoroutinefunction
import functools

from .task import Task
from .context import task_context


def task(func):
    @functools.wraps(func)
    async def wrapper_decorator(*args, **kwargs):
        token = task_context.set(task_instance)

        if iscoroutinefunction(func):
            value = await func(*args, **kwargs)
        else:
            value = func(*args, **kwargs)

        task_context.reset(token)

        return value

    task_instance = Task(
        id=func.__name__, description=func.__doc__, run=wrapper_decorator
    )

    return task_instance
