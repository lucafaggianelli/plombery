A pipeline is a graph of tasks: each task declares which tasks must run before
it, and Plombery runs them in that order, in parallel whenever the graph allows
it. The graph must be acyclic, and Plombery refuses to register a pipeline that
contains a cycle.

## Declaring the graph

The recommended way to build a pipeline is the `Pipeline` context manager: every
task defined inside it is added to the pipeline automatically, and dependencies
are declared with the `>>` operator.

```py
from plombery import Pipeline, task

with Pipeline(id="sales_pipeline") as pipeline:
    @task
    def extract():
        return [1, 2, 3]

    @task
    def transform(extract):
        return [value * 2 for value in extract]

    @task
    def notify(extract):
        ...

    # transform and notify both depend on extract, and run in parallel
    extract >> [transform, notify]
```

`a >> b` reads "a runs before b". The reverse operator is also available, so
`b << a` means the same thing. A task can depend on several tasks, and several
tasks can depend on it:

```py
extract >> transform >> load
extract >> notify
```

!!! warning "Dependencies are explicit"

    Defining tasks one after the other is not enough: two tasks with no `>>`
    between them have no relationship and will run at the same time. This is a
    breaking change from the versions of Plombery where `tasks=[a, b, c]` meant
    "run a, then b, then c".

## Fan-out: dynamic task mapping

A task can be run once per item of the collection returned by an upstream task,
which is useful to process a list of files, accounts or hosts in parallel:

```py
from plombery import MappingMode, Pipeline, task

with Pipeline(id="hosts"):
    @task
    def get_hosts():
        return ["a.example.com", "b.example.com"]

    @task(mapping_mode=MappingMode.FAN_OUT, map_upstream_id="get_hosts")
    def check(get_hosts):
        # runs once per host, receiving a single host
        ...

    get_hosts >> check
```

`MappingMode.FAN_OUT` splits the upstream collection and gives one item to each
instance. `MappingMode.CHAINED_FAN_OUT` keeps the mapping going: the task runs
once per instance of the upstream mapped task, inheriting its index, so a chain
of mapped tasks processes one item at a time end to end.

If the upstream task of a fan-out doesn't return a collection, the run fails.

## Registering a pipeline

`register_pipeline` is the alternative, flat way to declare a pipeline, and the
only 2 mandatory fields are `id` and `tasks`. Dependencies still have to be
declared with `>>`:

```py
from plombery import register_pipeline, task

class InputParams(BaseModel):
  some_value: int

@task
def get_sales_data():
  pass

register_pipeline(
    # (required) the id identifies the pipeline univocally
    id="sales_pipeline_2345",
    # (required) the list of tasks to execute
    tasks=[get_sales_data],
    # This pipeline is configurable via input parameters
    params=InputParams,
    # The name is optional, if absent it would be generated from the ID
    name="Sales pipeline",
    description="""This is a very useless pipeline""",
    # Triggers with schedules
    triggers=[
        Trigger(
            id="daily",
            name="Daily",
            description="Run the pipeline every day",
            # the input params value for this specific trigger
            params=InputParams(some_value=2),
            schedule=IntervalTrigger(
                days=1,
            ),
        )
    ],
)
```

## Parameters

A pipeline is configurable if it declares some input parameters in the registration
via the `params` argument:

```py
register_pipeline(
  # ...
  params=InputParams
)
```

The `InputParams` is a [Pydantic Model](https://docs.pydantic.dev/latest/usage/models/):

```py
class InputParams(BaseModel):
  some_value: int
```

If the pipeline has input parameters, when you click the manual run button,
the dialog will present a form to let you customize the input parameters:

<figure markdown>
  ![Manual run with parameters](assets/images/run-pipeline-dialog.png)
  <figcaption>Manual run with parameters</figcaption>
</figure>

The input form in the dialog is created automatically thanks to the Pydantic's
`BaseModel` that you declared in the pipeline.

Parameters are configurable also when you run a pipeline via the HTTP trigger,
just pass the parameters as JSON body in the HTTP request.
