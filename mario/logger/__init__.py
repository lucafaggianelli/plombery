import logging

from mario.logger.formatter import JsonFormatter


def get_logger(filename: str, task_id: str):
    json_handler = logging.FileHandler(filename)
    json_formatter = JsonFormatter(task_id)
    json_handler.setFormatter(json_formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(json_handler)

    return logger
