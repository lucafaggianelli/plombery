import logging

from plombery.database.models import PipelineRun
from plombery.logger.formatter import JsonFormatter
from plombery.logger.web_socket_handler import build_queue_handler
from plombery.orchestrator.data_storage import get_logs_filename
from plombery.pipeline.context import (
    run_context,
    task_run_context,
)


def get_logger() -> logging.LoggerAdapter:
    """Get a logger for a task or pipeline. This function uses contexts
    so it must be called within a task function or within the internal
    functions that run a pipeline.

    Returns:
        Logger: a logger instance
    """

    pipeline_run = run_context.get()
    task_run = task_run_context.get(None)

    filename = get_logs_filename(pipeline_run.id)

    json_formatter = JsonFormatter(
        pipeline=pipeline_run.pipeline_id,
        task=task_run.task_id if task_run else None,
        map_index=task_run.map_index if task_run else None,
    )

    json_handler = logging.FileHandler(filename)
    json_handler.setFormatter(json_formatter)

    # A handler of its own, because the formatter holds this logger's task and
    # map index: a shared handler would label log lines with whichever task
    # created a logger last.
    websocket_handler = build_queue_handler(json_formatter)

    # Create a logger that's unique for each pipeline run
    # and not simply for each pipeline, otherwise successive
    # runs will always use the same log file because
    # `json_handler` wouldn't be added the logger, because,
    # in turn, `logger` is always the same instance.
    #
    # This fixes issue #131:
    #   https://github.com/lucafaggianelli/plombery/issues/131
    logger_name = f"plombery.{pipeline_run.id}"

    # On top of that, create 2 different loggers: 1 for pipelines and
    # 1 for tasks and be sure they're not in a parent-child
    # relationships otherwise it will generate double logs
    if task_run:
        logger_name += f"-{task_run.task_id}"

        if task_run.map_index is not None:
            logger_name += f"-{task_run.map_index}"

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # The `getLogger` returns a previously created logger
    # if any, so be sure not to re-add the same handlers again
    if not logger.handlers:
        logger.addHandler(json_handler)
        logger.addHandler(websocket_handler)

    extra_log_info = {
        "pipeline": pipeline_run.pipeline_id,
        "run_id": pipeline_run.id,
        "task": task_run.task_id if task_run else None,
        "map_index": task_run.map_index if task_run else None,
    }

    return logging.LoggerAdapter(logger, extra_log_info)


def close_logger(pipeline_run: PipelineRun):
    """
    Close all the resources and file descriptors opened by the logger.
    Solves issue 491: https://github.com/lucafaggianelli/plombery/issues/491

    A run doesn't use a single logger: `get_logger` creates one for the pipeline
    (`plombery.<run_id>`) and one for every task, and every mapped instance of a
    task (`plombery.<run_id>-<task_id>[-<map_index>]`). All of them hold an open
    file descriptor, so all of them have to be closed, otherwise a pipeline that
    fans out over a large collection leaks one descriptor per item.

    Args:
        pipeline_run (PipelineRun): the run that has just finished
    """

    run_logger_name = f"plombery.{pipeline_run.id}"

    logger_names = [
        name
        for name in list(logging.Logger.manager.loggerDict)
        if name == run_logger_name or name.startswith(f"{run_logger_name}-")
    ]

    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)

        # Iterate over a copy: `removeHandler` mutates the list being iterated,
        # which would silently skip every other handler.
        for handler in list(logger.handlers):
            # Only the file handler owns a resource. The queue handler writes to
            # the queue shared with the listener thread, which outlives the run.
            if isinstance(handler, logging.FileHandler):
                handler.close()

            logger.removeHandler(handler)

        # Loggers are never garbage collected by the logging module, and a new
        # one is created for every run and every task: drop them explicitly or
        # a long running instance grows one entry per task run, forever.
        logging.Logger.manager.loggerDict.pop(logger_name, None)
