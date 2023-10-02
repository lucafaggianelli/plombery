import time

from pydantic import BaseModel

from plombery import register_pipeline, task, get_logger


class InputParams(BaseModel):
    what: str


@task
def sync_task():
    """
    This task is not async though it shouldn't block
    the rest of the app
    """
    get_logger().debug("Im going to sleep for 10secs")
    time.sleep(10)


register_pipeline(
    id="sync_pipeline",
    description="This pipeline contains a sync task",
    tasks=[sync_task],
    params=InputParams,
)
