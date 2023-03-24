import logging

from mario.constants import PIPELINE_RUN_LOGS_FILE
from mario.logger.formatter import JsonFormatter
from mario.orchestrator.data_storage import get_data_path
from mario.pipeline.context import task_context, run_context


def get_logger():
    task = task_context.get()
    pipeline_run = run_context.get()

    filename = get_data_path(pipeline_run.id) / PIPELINE_RUN_LOGS_FILE

    json_handler = logging.FileHandler(filename)
    json_formatter = JsonFormatter(task.id)
    json_handler.setFormatter(json_formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(json_handler)

    return logger
