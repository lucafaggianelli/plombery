from contextlib import contextmanager
from contextvars import ContextVar

from plombery.database.models import PipelineRun, TaskRun
from plombery.pipeline.pipeline import Pipeline, Task

pipeline_context: ContextVar[Pipeline] = ContextVar("pipeline")
task_context: ContextVar[Task] = ContextVar("task")
run_context: ContextVar[PipelineRun] = ContextVar("run")
task_run_context: ContextVar[TaskRun] = ContextVar("task_run")


@contextmanager
def use_context(
    *,
    pipeline: Pipeline | None = None,
    run: PipelineRun | None = None,
    task: Task | None = None,
    task_run: TaskRun | None = None,
):
    """Bind pipeline and task state to the contexts for the duration of a block.

    Anything left out keeps whatever value it already had, and every context
    bound here is restored on the way out, exceptions included: a task that
    fails must not leave its own identity behind, or the next task scheduled
    from that same context would log under its name.
    """

    tokens = [
        (context, context.set(value))
        for context, value in (
            (pipeline_context, pipeline),
            (run_context, run),
            (task_context, task),
            (task_run_context, task_run),
        )
        if value is not None
    ]

    try:
        yield
    finally:
        for context, token in reversed(tokens):
            context.reset(token)  # pyright: ignore[reportArgumentType]
