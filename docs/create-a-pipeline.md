# Create your first pipeline

Create a new folder in your project root with
a file named `app.py` (or any name you want) in it,
as in Python files should be in a top-level package.

This should be your folder structure:

``` { .sh .no-copy }
.
├─ .venv/ # virtual environment folder
└─ src/
   ├─ __init__.py # empty file needed to declare Python modules
   └─ app.py # entrypoint to the project
```

## Glossary

Before starting, let's define some naming so there will be no confusion!

* **Task**: a python function that performs some job, it's the base block for building a pipeline
* **Pipeline**: a graph of one or more *Task*s, a pipeline can be run via a schedule, manually, etc.
* **Trigger**: is the entrypoint to run a pipeline, a trigger can be a schedule, a webhook, a button on the web UI, etc.
* **Pipeline Run**: (sometimes simply referred as *Run*) is the result of running a pipeline

## Basic pipeline

### Create a task

A *Task* is the base block in Plombery and it's just a Python function that
performs an action, i.e. download some data from an HTTP API, runs a query on a DB, etc.

!!! info

    notice how the `@task` decorator is used to declare a task

```py title="src/app.py"
from datetime import datetime
from random import randint

from plombery import Pipeline, task, get_logger


with Pipeline(id="sales_pipeline") as pipeline:
    @task
    async def fetch_raw_sales_data():
        """Fetch latest 50 sales of the day"""

        # using Plombery logger your logs will be stored
        # and accessible on the web UI
        logger = get_logger()

        logger.debug("Fetching sales data...")

        sales = [
            {
                "price": randint(1, 1000),
                "store_id": randint(1, 10),
                "date": datetime.today(),
                "sku": randint(1, 50),
            }
            for _ in range(50)
        ]

        logger.info("Fetched %s sales data rows", len(sales))

        # Return the results of your task to have it stored
        # and accessible on the web UI
        # If you have other tasks, the output of a task is
        # passed to the following one
        return sales
```

Every task defined inside the `with Pipeline()` block is added to the
pipeline automatically — there's nothing else to declare for a single task.
See [Pipelines](pipelines.md) for how to add more tasks and declare
dependencies between them with `>>`.

### Register the pipeline and add a trigger

Register the pipeline, and give it a schedule with a `Trigger`:

```py title="src/app.py"
from apscheduler.triggers.interval import IntervalTrigger
from plombery import register_pipeline, Trigger

register_pipeline(pipeline)
```

To have Plombery run it automatically, add a trigger to the `Pipeline` itself:

```py title="src/app.py"
with Pipeline(
    id="sales_pipeline",
    description="Aggregate sales activity from all stores across the country",
    triggers=[
        Trigger(
            id="daily",
            name="Daily",
            description="Run the pipeline every day",
            schedule=IntervalTrigger(days=1),
        ),
    ],
) as pipeline:
    ...
```

A pipeline with no trigger can still be run manually from the web UI, or via
its HTTP endpoint.

### Start the app

Finally add this at the bottom of your file to start the app:

```py title="src/app.py"
from plombery import get_app

app = get_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("plombery:get_app", reload=True, factory=True)
```

Now your `src/app.py` should look like this:

??? Example "Click to see the full content of src/app.py"

    ```py title="src/app.py"
    from datetime import datetime
    from random import randint

    from apscheduler.triggers.interval import IntervalTrigger
    from plombery import Pipeline, Trigger, get_app, get_logger, register_pipeline, task


    with Pipeline(
        id="sales_pipeline",
        description="Aggregate sales activity from all stores across the country",
        triggers=[
            Trigger(
                id="daily",
                name="Daily",
                description="Run the pipeline every day",
                schedule=IntervalTrigger(days=1),
            ),
        ],
    ) as pipeline:
        @task
        async def fetch_raw_sales_data():
            """Fetch latest 50 sales of the day"""

            # using Plombery logger your logs will be stored
            # and accessible on the web UI
            logger = get_logger()

            logger.debug("Fetching sales data...")

            sales = [
                {
                    "price": randint(1, 1000),
                    "store_id": randint(1, 10),
                    "date": datetime.today(),
                    "sku": randint(1, 50),
                }
                for _ in range(50)
            ]

            logger.info("Fetched %s sales data rows", len(sales))

            # Return the results of your task to have it stored
            # and accessible on the web UI
            return sales

    register_pipeline(pipeline)

    app = get_app()

    if __name__ == "__main__":
        import uvicorn

        uvicorn.run("plombery:get_app", reload=True, factory=True)
    ```

### Run the app

Plombery is based on FastAPI so you can run it as a normal FastAPI app
via `uvicorn` (as in this example) or another ASGI web server.

So install `uvicorn` and run the app:

```sh
pip install uvicorn
python src/app.py
```

Now open the page [http://localhost:8000](http://localhost:8000){target=_blank} in your browser and enjoy!
