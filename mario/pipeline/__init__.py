from asyncio import iscoroutinefunction
import functools

from mario.pipeline.task import Task
from .context import task_context


def task(func):
    task_instance = Task()

    @functools.wraps(func)
    async def wrapper_decorator(*args, **kwargs):
        token = task_context.set(task_instance)

        if iscoroutinefunction(func):
            value = await func(*args, **kwargs)
        else:
            value = func(*args, **kwargs)

        task_context.reset(token)

        return value

    task_instance.run = wrapper_decorator

    return task_instance
