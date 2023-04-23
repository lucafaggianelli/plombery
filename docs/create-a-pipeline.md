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

A *Pipeline* contains a list of tasks and eventually a list of triggers,
so in your `app.py` add this:

```py
from datetime import datetime
from random import randint

from apscheduler.triggers.interval import IntervalTrigger
from mario import Mario, task, get_logger, Pipeline, Trigger


sales_pipeline = Pipeline(
    id="sales_pipeline",
    tasks = [fetch_raw_sales_data],
    triggers = [
        Trigger(
            id="daily",
            name="Daily",
            description="Run the pipeline every day",
            aps_trigger=IntervalTrigger(days=1),
        )
    ],
)
```

A *Task* is the base block in Mario Pype and it's just a Python function that
performs an action, i.e. download some data from an HTTP API, runs a query on a DB, etc.

This is the task `fetch_raw_sales_data` used in the `sales_pipeline` pipeline ... it doesn't do much,
but it showcases the basics:

!!! info

    notice how the `@task` decorator is used to declare a task

```py
@task
async def fetch_raw_sales_data():
    # using MarioPype logger your logs will be stored
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
```

Finally create a Mario instance and register the pipeline so
MarioPype knows it's there:

```py
app = Mario()

app.register_pipeline(dummy_pipeline)
```

### Run Mario Pype

Mario Pype is based on FastAPI so you can run it as a normal FastAPI app
via `uvicorn` or another ASGI web server:

```sh
pip install uvicorn
uvicorn src.app:app --reload
```

Now open the page [http://localhost:8000](http://localhost:8000) in your browser and enjoy!
