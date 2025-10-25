import logging

from plombery.logger.formatter import JsonFormatter
from plombery.logger.web_socket_handler import queue_handler
from plombery.orchestrator.data_storage import get_logs_filename
from plombery.pipeline.context import task_context, run_context, pipeline_context


def get_logger() -> logging.LoggerAdapter:
    """Get a logger for a task or pipeline. This function uses contexts
    so it must be called within a task function or within the internal
    functions that run a pipeline.

    Returns:
        Logger: a logger instance
    """

    pipeline = pipeline_context.get()
    task = task_context.get(None)
    pipeline_run = run_context.get()

    filename = get_logs_filename(pipeline_run.id)

    json_formatter = JsonFormatter(pipeline=pipeline.id, task=task.id if task else None)

    json_handler = logging.FileHandler(filename)
    json_handler.setFormatter(json_formatter)

    websocket_handler = queue_handler
    websocket_handler.setFormatter(json_formatter)

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
    if task:
        logger_name += f"-{task.id}"

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # The `getLogger` returns a previously created logger
    # if any, so be sure not to re-add the same handlers again
    if not logger.handlers:
        logger.addHandler(json_handler)
        logger.addHandler(websocket_handler)

    extra_log_info = {
        "pipeline": pipeline.id,
        "run_id": pipeline_run.id,
        "task": task.id if task else None,
    }

    return logging.LoggerAdapter(logger, extra_log_info)


def close_logger(logger: logging.LoggerAdapter):
    """
    Close all the resources and file descriptors opened by the logger.
    Solves issue 491: https://github.com/lucafaggianelli/plombery/issues/491

    Args:
        logger (logging.LoggerAdapter): logger obtained with get_logger
    """
    for handler in logger.logger.handlers:
        logger.logger.removeHandler(handler)
        handler.close()
