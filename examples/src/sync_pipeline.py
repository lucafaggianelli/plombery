import time

from mario import register_pipeline, task


@task
def sync_task():
    """
    This task is not async though it shouldn't block
    the rest of the app
    """
    time.sleep(10)


register_pipeline(
    id="sync_pipeline",
    description="This pipeline contains a sync task",
    tasks=[sync_task],
)
