from typing import Callable, Union
from asyncio import iscoroutinefunction
import functools

from .task import Task
from .context import task_context


def task(func: Union[Callable, functools.partial]):
    @functools.wraps(func)
    async def wrapper_decorator(*args, **kwargs):
        token = task_context.set(task_instance)

        if iscoroutinefunction(func):
            value = await func(*args, **kwargs)
        else:
            value = func(*args, **kwargs)

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
