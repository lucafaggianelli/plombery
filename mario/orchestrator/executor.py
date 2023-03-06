from asyncio import iscoroutinefunction
import asyncio
from datetime import datetime
from logging import Logger

import pandas
from pydantic import BaseModel

from mario.logger import get_logger
from mario.websocket import manager
from mario.database.models import PipelineRun
from mario.database.repository import create_pipeline_run, update_pipeline_run
from mario.database.schemas import PipelineRunCreate
from mario.orchestrator.data_storage import get_data_path, read_data
from mario.pipeline.pipeline import Pipeline, PipelineRunStatus, Trigger, Task


def _on_pipeline_start(pipeline: Pipeline, trigger: Trigger):
    pipeline_run = create_pipeline_run(
        PipelineRunCreate(
            start_time=datetime.now(),
            pipeline_id=pipeline.uuid,
            trigger_id=trigger.id,
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
    run = dict(
        id=pipeline_run.id,
        status=pipeline_run.status,
        start_time=pipeline_run.start_time.isoformat(),
        duration=pipeline_run.duration,
    )

    awaitable = manager.broadcast(
        type="run-update",
        data=dict(
            run=run,
            pipeline=pipeline_run.pipeline_id,
            trigger=pipeline_run.trigger_id,
        ),
    )

    asyncio.ensure_future(awaitable)


async def run(pipeline: Pipeline, trigger: Trigger):
    print(f"Executing pipeline `{pipeline.uuid}` via trigger `{trigger.id}`")

    pipeline_run = _on_pipeline_start(pipeline, trigger)

    log_filename = get_data_path(pipeline_run) / "task_run.log"

    input_params = trigger.params
    params = {}

    if pipeline.params:
        params = pipeline.params(**(input_params or {}))
    elif input_params:
        pipeline.logger.warning("This pipeline doesn't support input params")

    flowing_data = None

    for task in pipeline.tasks:
        logger = get_logger(log_filename, task.uuid)
        logger.info("Executing task", task.uuid)
        try:
            flowing_data = await _execute_task(
                task, flowing_data, logger, input_params, params
            )
        except Exception as e:
            # A task failed so the entire pipeline failed
            _on_pipeline_executed(pipeline_run, PipelineRunStatus.FAILED)
            logger.error(str(e))
            break

        # Store task output if the task succeeds
        if type(flowing_data) is pandas.DataFrame:
            flowing_data: pandas.DataFrame = flowing_data
            data_path = get_data_path(pipeline_run)

            flowing_data.to_json(data_path / f"{task.uuid}.json", orient="records")

    else:
        # All task succeeded so the entire pipeline succeeded
        _on_pipeline_executed(pipeline_run, PipelineRunStatus.COMPLETED)


async def _execute_task(
    task: Task,
    flowing_data,
    logger: Logger,
    input_params: dict = None,
    pipeline_params: BaseModel = None,
):
    params = pipeline_params

    if not pipeline_params and task.params:
        params = task.params(**(input_params or {}))

    task.logger = logger
    if iscoroutinefunction(task.run):
        result = await task.run(flowing_data, params=params)
    else:
        result = task.run(flowing_data, params=params)

    return result


def get_pipeline_run_logs(pipeline_run: PipelineRun):
    return read_data("task_run.log", pipeline_run).rstrip()


def get_pipeline_run_data(pipeline_run: PipelineRun, task: str):
    return read_data(f"{task}.json", pipeline_run)
