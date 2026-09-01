from plombery import task, Pipeline

with Pipeline(id="failing_pipeline", auto_register=False) as failing_pipeline:

    @task
    async def failing_task():
        raise ValueError("task failed")
