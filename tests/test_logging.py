from asyncio import sleep
import json
import pytest

from plombery import _Plombery as Plombery
from plombery.orchestrator import run_pipeline_now
from plombery.orchestrator.data_storage import read_logs_file
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

    await run_pipeline_now(pipeline1)

    await sleep(1)

    logs = get_parsed_logs(1)

    assert logs == [
        {
            "level": "INFO",
            "loggerName": "plombery.1",
            "message": "Executing pipeline `pipeline1` #1 via trigger `_manual`",
            "pipeline": "pipeline1",
            "task": None,
        },
        {
            "level": "INFO",
            "message": "Executing task pipe_1_task_1",
            "loggerName": "plombery.1",
            "pipeline": "pipeline1",
            "task": None,
        },
        {
            "level": "DEBUG",
            "message": "a debug log",
            "loggerName": "plombery.1-pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
        },
        {
            "level": "INFO",
            "message": "an info log",
            "loggerName": "plombery.1-pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
        },
        {
            "level": "WARNING",
            "message": "a warning log",
            "loggerName": "plombery.1-pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
        },
        {
            "level": "ERROR",
            "message": "an error log",
            "loggerName": "plombery.1-pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
        },
        {
            "level": "CRITICAL",
            "message": "a critical log",
            "loggerName": "plombery.1-pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
        },
    ]
