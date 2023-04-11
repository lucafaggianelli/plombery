from asyncio import sleep
import json
import pytest

from mario import Mario
from mario.orchestrator import run_pipeline_now
from mario.orchestrator.executor import get_pipeline_run_logs
from .pipeline_1 import Pipeline1


def _clean_log_message(log):
    del log["timestamp"]
    return log


def get_parsed_logs(run_id: int):
    logs = get_pipeline_run_logs(run_id)
    return [
        json.loads(log, object_hook=_clean_log_message) for log in logs.splitlines()
    ]


@pytest.mark.asyncio
async def test_pipeline_logs_are_correclty_captured():
    app = Mario()
    app.register_pipeline(pipeline := Pipeline1())

    await run_pipeline_now(pipeline)

    await sleep(1)

    logs = get_parsed_logs(1)

    assert logs == [
        {
            "level": "INFO",
            "message": "Executing task pipe_1_task_1",
            "loggerName": "mario.pipeline1",
            "pipeline": "pipeline1",
            "task": None,
        },
        {
            "level": "DEBUG",
            "message": "a debug log",
            "loggerName": "mario.pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
        },
        {
            "level": "INFO",
            "message": "an info log",
            "loggerName": "mario.pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
        },
        {
            "level": "WARNING",
            "message": "a warning log",
            "loggerName": "mario.pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
        },
        {
            "level": "ERROR",
            "message": "an error log",
            "loggerName": "mario.pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
        },
        {
            "level": "CRITICAL",
            "message": "a critical log",
            "loggerName": "mario.pipe_1_task_1",
            "pipeline": "pipeline1",
            "task": "pipe_1_task_1",
        },
    ]
