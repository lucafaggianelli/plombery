from asyncio import sleep
import json
import pytest

from plombery import _Plombery as Plombery
from plombery.database.repository import get_pipeline_run
from plombery.orchestrator import run_pipeline_now
from plombery.orchestrator.data_storage import read_logs_file
from .failing_pipeline import failing_pipeline
from .pipeline_1 import pipeline1


def _clean_log_message(log):
    del log["timestamp"]
    return log


def get_parsed_logs(run_id: int):
    logs = read_logs_file(run_id)
    return [
        json.loads(log, object_hook=_clean_log_message) for log in logs.splitlines()
    ]


@pytest.mark.asyncio
async def test_pipeline_logs_are_correclty_captured(app: Plombery):
    app.start()
    app.register_pipeline(pipeline1)

    run = await run_pipeline_now(pipeline1)
    run_id = run.id

    await sleep(1)

    pipeline_run = get_pipeline_run(run_id)
    task_run_id = pipeline_run.task_runs[0].id

    logs = get_parsed_logs(run_id)

    assert logs == [
        {
            "level": "INFO",
            "loggerName": f"plombery.{run_id}",
            "message": f"Executing pipeline `pipeline1` #{run_id} via trigger `_manual`",
            "pipeline": "pipeline1",
            "task": None,
            "map_index": None,
        },
        {
            "level": "INFO",
            "message": f"Executing task pipe_1_task_1 in pipeline pipeline1 (id={task_run_id})",
            "loggerName": f"plombery.{run_id}-pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
            "map_index": None,
        },
        {
            "level": "DEBUG",
            "message": "a debug log",
            "loggerName": f"plombery.{run_id}-pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
            "map_index": None,
        },
        {
            "level": "INFO",
            "message": "an info log",
            "loggerName": f"plombery.{run_id}-pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
            "map_index": None,
        },
        {
            "level": "WARNING",
            "message": "a warning log",
            "loggerName": f"plombery.{run_id}-pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
            "map_index": None,
        },
        {
            "level": "ERROR",
            "message": "an error log",
            "loggerName": f"plombery.{run_id}-pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
            "map_index": None,
        },
        {
            "level": "CRITICAL",
            "message": "a critical log",
            "loggerName": f"plombery.{run_id}-pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
            "map_index": None,
        },
    ]


@pytest.mark.asyncio
async def test_failing_task_logs_are_attributed_to_the_task(app: Plombery):
    """The error logged when a task raises belongs to that task.

    It's the line one goes looking for first, and a log without a task on it
    doesn't say which task of the pipeline failed.
    """

    app.start()
    app.register_pipeline(failing_pipeline)

    run = await run_pipeline_now(failing_pipeline)

    await sleep(1)

    errors = [log for log in get_parsed_logs(run.id) if log["level"] == "ERROR"]

    assert len(errors) == 1
    assert errors[0]["message"] == "task failed"
    assert errors[0]["task"] == "failing_task"
    assert errors[0]["loggerName"] == f"plombery.{run.id}-failing_task"
