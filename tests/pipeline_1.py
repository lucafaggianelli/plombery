from plombery import task, Pipeline, get_logger


@task
async def pipe_1_task_1(data, params=None):
    logger = get_logger()

    logger.debug("a debug log")
    logger.info("an info log")
    logger.warning("a warning log")
    logger.error("an error log")
    logger.critical("a critical log")


pipeline1 = Pipeline(id="pipeline1", tasks=[pipe_1_task_1])

pipeline1_serialized = {
    "id": "pipeline1",
    "name": "Pipeline1",
    "description": None,
    "tasks": [
        {
            "id": "pipe_1_task_1",
            "name": "Pipe 1 Task 1",
            "description": None,
        }
    ],
    "triggers": [],
}
