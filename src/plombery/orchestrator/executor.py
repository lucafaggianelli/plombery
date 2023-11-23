from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timezone
import inspect

from pydantic import BaseModel

from plombery.constants import MANUAL_TRIGGER_ID
from plombery.exceptions import InvalidDataPath
from plombery.logger import get_logger
from plombery.notifications import notification_manager
from plombery.utils import run_all_coroutines
from plombery.websocket import sio
from plombery.database.models import PipelineRun
from plombery.database.repository import create_pipeline_run, update_pipeline_run
from plombery.database.schemas import PipelineRunCreate
from plombery.orchestrator.data_storage import store_task_output
from plombery.pipeline.pipeline import Pipeline, Trigger, Task
from plombery.pipeline.context import pipeline_context, run_context
from plombery.schemas import PipelineRunStatus, TaskRun


def utcnow():
    return datetime.now(tz=timezone.utc)


def _on_pipeline_start(pipeline: Pipeline, trigger: Optional[Trigger] = None):
    pipeline_run = create_pipeline_run(
        PipelineRunCreate(
            start_time=utcnow(),
            pipeline_id=pipeline.id,
            trigger_id=trigger.id if trigger else MANUAL_TRIGGER_ID,
            status=PipelineRunStatus.RUNNING,
        )
    )

    _send_pipeline_event(pipeline, pipeline_run)

    return pipeline_run


def _on_pipeline_status_changed(
    pipeline: Pipeline, pipeline_run: PipelineRun, status: PipelineRunStatus
):
    update_pipeline_run(pipeline_run, utcnow(), status)

    _send_pipeline_event(pipeline, pipeline_run)

    return pipeline_run


def _send_pipeline_event(pipeline: Pipeline, pipeline_run: PipelineRun):
    notify_coro = notification_manager.notify(pipeline, pipeline_run)

    run = dict(
        id=pipeline_run.id,
        status=pipeline_run.status,
        start_time=pipeline_run.start_time.isoformat(),
        duration=pipeline_run.duration,
    )

    emit_coro = sio.emit(
        "run-update",
        dict(
            run=run,
            pipeline=pipeline_run.pipeline_id,
            trigger=pipeline_run.trigger_id,
        ),
    )

    run_all_coroutines([notify_coro, emit_coro])


async def run(
    pipeline: Pipeline,
    trigger: Optional[Trigger] = None,
    params: Optional[Dict[str, Any]] = None,
    pipeline_run: Optional[PipelineRun] = None,
):
    """
    This is the function that actually runs the pipeline, running all its tasks.

    `pipeline_run` is typically supplied when the pipeline is run manually,
        in this case one wants to know immediately the run_id to follow
        the execution of the pipeline.
    """

    if pipeline_run:
        _on_pipeline_status_changed(pipeline, pipeline_run, PipelineRunStatus.RUNNING)
    else:
        pipeline_run = _on_pipeline_start(pipeline, trigger)

    pipeline_run.tasks_run = []

    pipeline_token = pipeline_context.set(pipeline)
    run_token = run_context.set(pipeline_run)

    logger = get_logger()

    logger.info(
        "Executing pipeline `%s` #%d via trigger `%s`",
        pipeline.id,
        pipeline_run.id,
        trigger.id if trigger else MANUAL_TRIGGER_ID,
    )

    pipeline_params: Optional[BaseModel] = None

    if pipeline.params:
        pipeline_params = (
            trigger.params if trigger else pipeline.params(**(params or {}))
        )
    elif (trigger and trigger.params) or params:
        logger.warning("This pipeline doesn't support input params")

    flowing_data = None

    for task in pipeline.tasks:
        logger.info("Executing task %s", task.id)

        task_run = TaskRun(task_id=task.id)

        task_start_time = utcnow()

        try:
            flowing_data = await _execute_task(task, flowing_data, pipeline_params)
            task_run.status = PipelineRunStatus.COMPLETED
        except Exception as e:
            logger.error(str(e), exc_info=e)
            flowing_data = None
            task_run.status = PipelineRunStatus.FAILED
        finally:
            task_run.duration = (utcnow() - task_start_time).total_seconds() * 1000

            try:
                task_run.has_output = store_task_output(
                    pipeline_run.id, task.id, flowing_data
                )
            except InvalidDataPath as error:
                logger.error(
                    "Can't store the task output as the path is invalid", exc_info=error
                )

            pipeline_run.tasks_run.append(task_run)

            if task_run.status == PipelineRunStatus.FAILED:
                # A task failed so the entire pipeline failed
                _on_pipeline_status_changed(
                    pipeline, pipeline_run, PipelineRunStatus.FAILED
                )
                break

    else:
        # All task succeeded so the entire pipeline succeeded
        _on_pipeline_status_changed(pipeline, pipeline_run, PipelineRunStatus.COMPLETED)

    pipeline_context.reset(pipeline_token)
    run_context.reset(run_token)


@dataclass
class TaskFunctionSignature:
    has_positional_args: bool = False
    has_params_arg: bool = False


def check_task_signature(func: Callable) -> TaskFunctionSignature:
    """
    Check if a function signature declares positional args.

    This is meant to be used to check if a task function
    accepts data inputs from another task
    """

    result = TaskFunctionSignature()

    for name, parameter in inspect.signature(func).parameters.items():
        if (
            parameter.kind == inspect.Parameter.POSITIONAL_ONLY
            or inspect.Parameter.VAR_POSITIONAL
        ) and name != "params":
            result.has_positional_args = True
        elif parameter.VAR_KEYWORD or (parameter.KEYWORD_ONLY and name == "params"):
            result.has_params_arg = True

    return result


async def _execute_task(
    task: Task,
    flowing_data,
    params: Optional[BaseModel] = None,
):
    result = check_task_signature(task.run)

    args = [flowing_data] if result.has_positional_args else []
    kwargs = {"params": params} if params and result.has_params_arg else {}

    result = await task.run(*args, **kwargs)

    return result
