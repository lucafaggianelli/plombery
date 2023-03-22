from contextvars import ContextVar

from mario.database.models import PipelineRun
from mario.pipeline.pipeline import Pipeline, Task


pipeline_context: ContextVar[Pipeline] = ContextVar('pipeline')
task_context: ContextVar[Task] = ContextVar('task')
run_context: ContextVar[PipelineRun] = ContextVar('run')
