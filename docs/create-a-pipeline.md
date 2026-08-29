# Create your first pipeline

Plombery discovers your pipelines from a `pipelines/` folder and runs them with
the `plombery` command. A minimal project is just that folder with one file in
it:

``` { .sh .no-copy }
.
├─ .venv/          # virtual environment folder
└─ pipelines/
   └─ sales.py     # a pipeline
```

## Glossary

Before starting, let's define some naming so there will be no confusion!

* **Task**: a python function that performs some job, it's the base block for building a pipeline
* **Pipeline**: a graph of one or more *Task*s, a pipeline can be run via a schedule, manually, etc.
* **Trigger**: is the entrypoint to run a pipeline, a trigger can be a schedule, a webhook, a button on the web UI, etc.
* **Pipeline Run**: (sometimes simply referred as *Run*) is the result of running a pipeline

## Write a pipeline

Create `pipelines/sales.py`. A *Task* is a Python function decorated with
`@task`; a *Pipeline* groups the tasks defined inside its `with` block; and
`register_pipeline` makes Plombery aware of it.

```py title="pipelines/sales.py"
from datetime import datetime
from random import randint

from plombery import Pipeline, register_pipeline, task, get_logger


with Pipeline(id="sales_pipeline") as pipeline:
    @task
    async def fetch_raw_sales_data():
        """Fetch latest 50 sales of the day"""

        # Using Plombery's logger, your logs are stored and shown in the web UI
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

        # Returning a value stores it and makes it available in the web UI;
        # it's also passed to any task downstream of this one
        return sales


register_pipeline(pipeline)
```

Every task defined inside the `with Pipeline()` block is added to the pipeline
automatically. See [Pipelines](pipelines.md) for how to add more tasks and
declare dependencies between them with `>>`.

## Run it

```sh
plombery run
```

`plombery run` imports every file in the `pipelines/` folder, so each
`register_pipeline` runs, and serves the web app. Open
[http://localhost:8000](http://localhost:8000){target=_blank} and you'll find
your pipeline, ready to run manually.

By default it looks for a `pipelines/` folder in the current directory and
binds to `127.0.0.1:8000`. Change any of that:

```sh
plombery run --pipelines flows --host 0.0.0.0 --port 9000
```

## Schedule it

A pipeline with no trigger can be run manually from the web UI or its HTTP
endpoint. To have Plombery run it on a schedule, add a `Trigger`:

```py title="pipelines/sales.py"
from apscheduler.triggers.interval import IntervalTrigger
from plombery import Pipeline, Trigger, register_pipeline, task


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
        ...


register_pipeline(pipeline)
```

See [Triggers](triggers.md) for cron schedules and triggers with parameters.

## Without the CLI

`plombery run` is the quickest way to start, but Plombery is a FastAPI app, so
you can also run it yourself — useful to embed it in a larger app, or to use a
different ASGI server. Import your pipelines, expose the app with `get_app()`,
and serve it:

```py title="app.py"
from plombery import get_app

# import the modules that register pipelines
import pipelines.sales  # noqa: F401

app = get_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
```

```sh
python app.py
```
