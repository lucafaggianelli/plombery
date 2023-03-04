from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO

import pandas
from pydantic import BaseModel

from mario.database.models import PipelineRun
from mario.database.repository import create_pipeline_run
from mario.database.schemas import PipelineRunCreate
from mario.orchestrator.data_storage import get_data_path, store_data, read_data
from mario.pipeline.pipeline import Pipeline, Trigger, Task


def run(pipeline: Pipeline, trigger: Trigger):
    log_out = StringIO()

    print(f"Executing pipeline {pipeline.uuid} via trigger {trigger.name}")

    pipeline_run = create_pipeline_run(
        PipelineRunCreate(
            start_time=datetime.now(),
            pipeline_id=pipeline.uuid,
            trigger_id=trigger.name,
            status="running",
        )
    )

    input_params = trigger.params

    if pipeline.params:
        params = pipeline.params(**(input_params or {}))
    elif input_params:
        pipeline.logger.warning("This pipeline doesn't support input params")

    flowing_data = None

    for task in pipeline.tasks:
        print("Executing task", task.uuid)
        flowing_data = _execute_task(task, flowing_data, log_out, input_params, params)

        # Store task output
        if type(flowing_data) is pandas.DataFrame:
            flowing_data: pandas.DataFrame = flowing_data
            data_path = get_data_path(pipeline_run)

            flowing_data.to_json(data_path / f"{task.uuid}.json", orient="records")

    # Store logs
    store_data("task_run.log", log_out.getvalue(), pipeline_run)
    log_out.close()


def _execute_task(
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
        result = task.run(flowing_data, params=params)

    return result


def get_pipeline_run_logs(pipeline_run: PipelineRun):
    return read_data("task_run.log", pipeline_run)


def get_pipeline_run_data(pipeline_run: PipelineRun, task: str):
    return read_data(f"{task}.json", pipeline_run)
