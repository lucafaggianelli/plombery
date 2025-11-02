from contextvars import ContextVar

from plombery.database.models import PipelineRun, TaskRun
from plombery.pipeline.pipeline import Pipeline, Task


pipeline_context: ContextVar[Pipeline] = ContextVar("pipeline")
task_context: ContextVar[Task] = ContextVar("task")
run_context: ContextVar[PipelineRun] = ContextVar("run")
task_run_context: ContextVar[TaskRun] = ContextVar("task_run")
