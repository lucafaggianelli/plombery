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
* **Pipeline**: a sequence of 1 or more *Task*s, a pipeline can be run via a schedule, manually, etc.
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

from apscheduler.triggers.interval import IntervalTrigger
from plombery import task, get_logger, Trigger, register_pipeline


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

### Create a pipeline

A *Pipeline* contains a list of tasks and eventually a list of triggers,
so in your `app.py` add this:

```py title="src/app.py"
register_pipeline(
    id="sales_pipeline",
    description="Aggregate sales activity from all stores across the country",
    tasks = [fetch_raw_sales_data],
    triggers = [
        Trigger(
            id="daily",
            name="Daily",
            description="Run the pipeline every day",
            schedule=IntervalTrigger(days=1),
        ),
    ],
)
```

Finally add this at the bottom of your file to start the app:

```py title="src/app.py"
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
    from plombery import task, get_logger, Trigger, register_pipeline


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


    register_pipeline(
        id="sales_pipeline",
        description="Aggregate sales activity from all stores across the country",
        tasks=[fetch_raw_sales_data],
        triggers=[
            Trigger(
                id="daily",
                name="Daily",
                description="Run the pipeline every day",
                schedule=IntervalTrigger(days=1),
            ),
        ],
    )

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
