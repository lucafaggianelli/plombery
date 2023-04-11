from mario import task, Pipeline, get_logger


@task
async def pipe_1_task_1(data, params=None):
    logger = get_logger()

    logger.debug("a debug log")
    logger.info("an info log")
    logger.warning("a warning log")
    logger.error("an error log")
    logger.critical("a critical log")


class Pipeline1(Pipeline):
    tasks = [pipe_1_task_1]
