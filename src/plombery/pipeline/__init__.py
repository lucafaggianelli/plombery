import asyncio
import functools
from typing import Callable, Union

from .task import Task
from .context import task_context


def task(func: Union[Callable, functools.partial]):
    @functools.wraps(func)
    async def wrapper_decorator(*args, **kwargs):
        token = task_context.set(task_instance)

        if asyncio.iscoroutinefunction(func):
            value = await func(*args, **kwargs)
        else:
            # Run in thread rather than in event loop to propagate context
            # to sync functions as well.
            #
            # This fixes:
            # https://github.com/lucafaggianelli/plombery/issues/153
            value = await asyncio.to_thread(func, *args, **kwargs)

        task_context.reset(token)

        return value

    if isinstance(func, functools.partial):
        id = func.func.__name__
        description = func.func.__doc__
    else:
        id = func.__name__
        description = func.__doc__

    task_instance = Task(id=id, description=description, run=wrapper_decorator)

    return task_instance
