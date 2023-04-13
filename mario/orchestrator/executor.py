from asyncio import iscoroutinefunction
import asyncio
from datetime import datetime
from typing import Coroutine, Dict, List

from pydantic import BaseModel

from mario.constants import MANUAL_TRIGGER_ID
from mario.logger import get_logger
from mario.notifications import notification_manager
from mario.websocket import manager
from mario.database.models import PipelineRun
from mario.database.repository import create_pipeline_run, update_pipeline_run
from mario.database.schemas import PipelineRunCreate
from mario.orchestrator.data_storage import (
    read_logs_file,
    read_task_run_data,
    store_task_output,
)
from mario.pipeline.pipeline import Pipeline, Trigger, Task
from mario.pipeline.context import pipeline_context, run_context
from mario.schemas import PipelineRunStatus, TaskRun


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
    pipeline_run.tasks_run: Dict[str, TaskRun] = dict()

    pipeline_token = pipeline_context.set(pipeline)
    run_token = run_context.set(pipeline_run)

    input_params = trigger.params if trigger else params
    params = {}

    logger = get_logger()

    if pipeline.params:
        params = pipeline.params(**(input_params or {}))
    elif input_params:
        logger.warning("This pipeline doesn't support input params")

    flowing_data = None

    for task in pipeline.tasks:
        logger.info("Executing task %s", task.id)

        task_run = TaskRun()

        try:
            task_start_time = datetime.now()
            flowing_data = await _execute_task(task, flowing_data, input_params, params)
            task_run.status = PipelineRunStatus.COMPLETED
        except Exception as e:
            logger.error(str(e), exc_info=e)

            # A task failed so the entire pipeline failed
            task_run.status = PipelineRunStatus.FAILED
            _on_pipeline_executed(pipeline_run, PipelineRunStatus.FAILED)
            break
        finally:
            task_run.duration = (datetime.now() - task_start_time).total_seconds() * 1000
            task_run.has_output = store_task_output(pipeline_run.id, task.id, flowing_data)

            pipeline_run.tasks_run[task.id] = task_run

    else:
        # All task succeeded so the entire pipeline succeeded
        _on_pipeline_executed(pipeline_run, PipelineRunStatus.COMPLETED)

    pipeline_context.reset(pipeline_token)
    run_context.reset(run_token)


async def _execute_task(
    task: Task,
    flowing_data,
    input_params: dict = None,
    pipeline_params: BaseModel = None,
):
    params = pipeline_params

    if not pipeline_params and task.params:
        params = task.params(**(input_params or {}))

    if iscoroutinefunction(task.run):
        result = await task.run(flowing_data, params=params)
    else:
        result = task.run(flowing_data, params=params)

    return result


def get_pipeline_run_logs(pipeline_run_id: int):
    return read_logs_file(pipeline_run_id)


def get_pipeline_run_data(pipeline_run_id: int, task_id: str):
    return read_task_run_data(pipeline_run_id, task_id)
