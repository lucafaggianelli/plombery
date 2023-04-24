import time

from mario import Pipeline, task


@task
def sync_task():
    """
    This task is not async though it shouldn't block
    the rest of the app
    """
    time.sleep(10)


sync_pipeline = Pipeline(
    id="sync_pipeline", description="This pipeline contains a sync task", tasks=[sync_task]
)
