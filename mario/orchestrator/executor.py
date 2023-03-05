from asyncio import iscoroutinefunction
import asyncio
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO

import pandas
from pydantic import BaseModel

from mario.websocket import manager
from mario.database.models import PipelineRun
from mario.database.repository import create_pipeline_run, update_pipeline_run
from mario.database.schemas import PipelineRunCreate
from mario.orchestrator.data_storage import get_data_path, store_data, read_data
from mario.pipeline.pipeline import Pipeline, Trigger, Task


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


def _on_pipeline_completed(pipeline_run: PipelineRun, status: str):
    update_pipeline_run(
        pipeline_run, datetime.now(), status
    )

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
    log_out = StringIO()

    print(f"Executing pipeline `{pipeline.uuid}` via trigger `{trigger.id}`")

    pipeline_run = _on_pipeline_start(pipeline, trigger)

    input_params = trigger.params
    params = {}

    if pipeline.params:
        params = pipeline.params(**(input_params or {}))
    elif input_params:
        pipeline.logger.warning("This pipeline doesn't support input params")

    flowing_data = None

    for task in pipeline.tasks:
        print("Executing task", task.uuid)
        try:
            flowing_data = await _execute_task(
                task, flowing_data, log_out, input_params, params
            )
        except Exception as e:
            _on_pipeline_completed(pipeline_run, "fail")
            log_out.writelines([str(e)])
            return

        # Store task output
        if type(flowing_data) is pandas.DataFrame:
            flowing_data: pandas.DataFrame = flowing_data
            data_path = get_data_path(pipeline_run)

            flowing_data.to_json(data_path / f"{task.uuid}.json", orient="records")

    _on_pipeline_completed(pipeline_run.id, pipeline_run.start_time, "success")

    # Store logs
    store_data("task_run.log", log_out.getvalue(), pipeline_run)
    log_out.close()


async def _execute_task(
    task: Task,
    flowing_data,
    log_out: StringIO,
    input_params: dict = None,
    pipeline_params: BaseModel = None,
):
    params = pipeline_params

    if not pipeline_params and task.params:
        params = task.params(**(input_params or {}))

    with redirect_stdout(log_out):
        if iscoroutinefunction(task.run):
            result = await task.run(flowing_data, params=params)
        else:
            result = task.run(flowing_data, params=params)

    return result


def get_pipeline_run_logs(pipeline_run: PipelineRun):
    return read_data("task_run.log", pipeline_run)


def get_pipeline_run_data(pipeline_run: PipelineRun, task: str):
    return read_data(f"{task}.json", pipeline_run)
