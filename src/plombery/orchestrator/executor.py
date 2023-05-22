from typing import Callable, Coroutine, List
import asyncio
from datetime import datetime
import inspect

from pydantic import BaseModel

from plombery.constants import MANUAL_TRIGGER_ID
from plombery.logger import get_logger
from plombery.notifications import notification_manager
from plombery.websocket import manager
from plombery.database.models import PipelineRun
from plombery.database.repository import create_pipeline_run, update_pipeline_run
from plombery.database.schemas import PipelineRunCreate
from plombery.orchestrator.data_storage import (
    read_logs_file,
    read_task_run_data,
    store_task_output,
)
from plombery.pipeline.pipeline import Pipeline, Trigger, Task
from plombery.pipeline.context import pipeline_context, run_context
from plombery.schemas import PipelineRunStatus, TaskRun


def _run_all_tasks(coros: List[Coroutine]):
    tasks = set()

    for coro in coros:
        task = asyncio.create_task(coro)

        tasks.add(task)
        task.add_done_callback(tasks.discard)


def _on_pipeline_start(pipeline: Pipeline, trigger: Trigger = None):
    pipeline_run = create_pipeline_run(
        PipelineRunCreate(
            start_time=datetime.now(),
            pipeline_id=pipeline.id,
            trigger_id=trigger.id if trigger else MANUAL_TRIGGER_ID,
            status="running",
        )
    )

    _send_pipeline_event(pipeline_run)

    return pipeline_run


def _on_pipeline_executed(pipeline_run: PipelineRun, status: PipelineRunStatus):
    update_pipeline_run(pipeline_run, datetime.now(), status)

    _send_pipeline_event(pipeline_run)

    return pipeline_run


def _send_pipeline_event(pipeline_run: PipelineRun):
    notify_coro = notification_manager.notify(pipeline_run)

    run = dict(
        id=pipeline_run.id,
        status=pipeline_run.status,
        start_time=pipeline_run.start_time.isoformat(),
        duration=pipeline_run.duration,
    )

    ws_coro = manager.broadcast(
        type="run-update",
        data=dict(
            run=run,
            pipeline=pipeline_run.pipeline_id,
            trigger=pipeline_run.trigger_id,
        ),
    )

    _run_all_tasks([notify_coro, ws_coro])


async def run(pipeline: Pipeline, trigger: Trigger = None, params: dict = None):
    print(
        f"Executing pipeline `{pipeline.id}` via trigger `{trigger.id if trigger else MANUAL_TRIGGER_ID}`"
    )

    pipeline_run = _on_pipeline_start(pipeline, trigger)
    pipeline_run.tasks_run = []

    pipeline_token = pipeline_context.set(pipeline)
    run_token = run_context.set(pipeline_run)

    input_params = trigger.params if trigger else params
    params = None

    logger = get_logger()

    if pipeline.params:
        params = pipeline.params(**(input_params or {}))
    elif input_params:
        logger.warning("This pipeline doesn't support input params")

    flowing_data = None

    for task in pipeline.tasks:
        logger.info("Executing task %s", task.id)

        task_run = TaskRun(task_id=task.id)

        try:
            task_start_time = datetime.now()
            flowing_data = await _execute_task(task, flowing_data, params)
            task_run.status = PipelineRunStatus.COMPLETED
        except Exception as e:
            logger.error(str(e), exc_info=e)
            flowing_data = None
            task_run.status = PipelineRunStatus.FAILED
        finally:
            task_run.duration = (
                datetime.now() - task_start_time
            ).total_seconds() * 1000

            task_run.has_output = store_task_output(
                pipeline_run.id, task.id, flowing_data
            )

            pipeline_run.tasks_run.append(task_run)

            if task_run.status == PipelineRunStatus.FAILED:
                # A task failed so the entire pipeline failed
                _on_pipeline_executed(pipeline_run, PipelineRunStatus.FAILED)
                break

    else:
        # All task succeeded so the entire pipeline succeeded
        _on_pipeline_executed(pipeline_run, PipelineRunStatus.COMPLETED)

    pipeline_context.reset(pipeline_token)
    run_context.reset(run_token)


def _has_positional_args(func: Callable) -> bool:
    """
    Check if a function signature declares positional args.

    This is meant to be used to check if a task function
    accepts data inputs from another task
    """

    for name, parameter in inspect.signature(func).parameters.items():
        if (
            parameter.kind == inspect.Parameter.POSITIONAL_ONLY
            or inspect.Parameter.VAR_POSITIONAL
        ) and name != "params":
            return True

    return False


async def _execute_task(
    task: Task,
    flowing_data,
    params: BaseModel = None,
):
    args = [flowing_data] if _has_positional_args(task.run) else []
    kwargs = {"params": params} if params else {}

    if asyncio.iscoroutinefunction(task.run):
        result = await task.run(*args, **kwargs)
    else:
        result = task.run(*args, **kwargs)

    return result


def get_pipeline_run_logs(pipeline_run_id: int):
    return read_logs_file(pipeline_run_id)


def get_pipeline_run_data(pipeline_run_id: int, task_id: str):
    return read_task_run_data(pipeline_run_id, task_id)
