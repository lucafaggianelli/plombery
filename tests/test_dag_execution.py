"""End to end tests for the DAG execution semantics.

These cover how the orchestrator walks the graph: how data flows between tasks,
how fan-out and fan-in behave, and what happens when something goes wrong.
"""

import asyncio
from typing import List

import pytest

from plombery import Pipeline, task, _Plombery as Plombery
from plombery.orchestrator import run_pipeline_now
from plombery.pipeline.tasks import MappingMode
from plombery.schemas import PipelineRunStatus

from .conftest import count_task_runs, wait_for_run


@pytest.mark.asyncio
async def test_linear_dag_flows_data(app: Plombery):
    app.start()

    with Pipeline(id="linear") as pipeline:

        @task
        def first():
            return 1

        @task
        def second(first):
            return first + 1

        first >> second

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED
    assert count_task_runs(run) == {"first": 1, "second": 1}


@pytest.mark.asyncio
async def test_task_receives_data_from_every_upstream(app: Plombery):
    received = []

    app.start()

    with Pipeline(id="multi-upstream") as pipeline:

        @task
        def left():
            return "L"

        @task
        def right():
            return "R"

        @task
        def join(left, right):
            received.append((left, right))

        left >> join
        right >> join

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED
    assert received == [("L", "R")]


@pytest.mark.asyncio
async def test_diamond_runs_the_join_task_only_once(app: Plombery):
    """A >> [B, C] >> D: D must wait for both branches and run exactly once."""

    calls = []

    app.start()

    with Pipeline(id="diamond") as pipeline:

        @task
        def start():
            return 1

        @task
        async def branch_a(start):
            await asyncio.sleep(0.01)
            return "a"

        @task
        async def branch_b(start):
            await asyncio.sleep(0.01)
            return "b"

        @task
        def join(branch_a, branch_b):
            calls.append((branch_a, branch_b))

        start >> [branch_a, branch_b]
        branch_a >> join
        branch_b >> join

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED
    assert calls == [("a", "b")]
    assert count_task_runs(run)["join"] == 1


@pytest.mark.asyncio
async def test_fan_out_runs_a_task_instance_per_item(app: Plombery):
    received = []

    app.start()

    with Pipeline(id="fan-out") as pipeline:

        @task
        def source():
            return [1, 2, 3]

        @task(mapping_mode=MappingMode.FAN_OUT, map_upstream_id="source")
        def each(source):
            received.append(source)
            return source * 10

        source >> each

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED
    assert sorted(received) == [1, 2, 3]
    assert count_task_runs(run) == {"source": 1, "each": 3}


@pytest.mark.asyncio
async def test_fan_in_gathers_the_output_of_every_mapped_instance(app: Plombery):
    """A non mapped task downstream of a fan-out collects all of its outputs.

    Regression test: the mapped task runs are stored under `task_id.map_index`,
    so looking them up by plain task ID used to miss them and silently pass
    `None` to the downstream task, throwing away the whole fan-out result.
    """

    received = []

    app.start()

    with Pipeline(id="fan-in") as pipeline:

        @task
        def source():
            return [1, 2, 3]

        @task(mapping_mode=MappingMode.FAN_OUT, map_upstream_id="source")
        async def each(source):
            await asyncio.sleep(0.01)
            return source * 10

        @task
        def gather(each):
            received.append(each)

        source >> each >> gather

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED
    assert received == [[10, 20, 30]], "fan-in must gather every mapped output"
    assert count_task_runs(run)["gather"] == 1


@pytest.mark.asyncio
async def test_chained_fan_out_inherits_the_map_index(app: Plombery):
    received = []

    app.start()

    with Pipeline(id="chained-fan-out") as pipeline:

        @task
        def source():
            return [1, 2, 3]

        @task(mapping_mode=MappingMode.FAN_OUT, map_upstream_id="source")
        def double(source):
            return source * 2

        @task(mapping_mode=MappingMode.CHAINED_FAN_OUT, map_upstream_id="double")
        def increment(double):
            received.append(double)
            return double + 1

        source >> double >> increment

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED
    assert sorted(received) == [2, 4, 6]
    assert count_task_runs(run) == {"source": 1, "double": 3, "increment": 3}


@pytest.mark.asyncio
async def test_fan_out_over_a_non_collection_fails_the_run(app: Plombery):
    """A fan-out task whose upstream isn't a collection must fail, not hang.

    Regression test: the orchestration error used to escape the executor while
    the run was still marked RUNNING, and nothing would ever advance the DAG
    again, leaving the run pending forever.
    """

    app.start()

    with Pipeline(id="bad-fan-out") as pipeline:

        @task
        def source():
            return {"not": "a collection"}

        @task(mapping_mode=MappingMode.FAN_OUT, map_upstream_id="source")
        def each(source):
            return source

        source >> each

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id, timeout=5)

    assert run.status == PipelineRunStatus.FAILED


@pytest.mark.asyncio
async def test_failing_task_fails_the_run_and_stops_downstream(app: Plombery):
    downstream_calls = []

    app.start()

    with Pipeline(id="failing") as pipeline:

        @task
        def boom():
            raise ValueError("boom")

        @task
        def downstream(boom):
            downstream_calls.append(1)

        boom >> downstream

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id, timeout=5)

    assert run.status == PipelineRunStatus.FAILED
    assert downstream_calls == []


@pytest.mark.asyncio
async def test_argument_with_a_default_is_not_an_upstream_task(app: Plombery):
    """Regression test: an argument that doesn't name an upstream task but has a
    default used to be overwritten with `None`, shadowing the default."""

    received = []

    app.start()

    with Pipeline(id="default-arg") as pipeline:

        @task
        def source():
            return 2

        @task
        def multiply(source, factor=10):
            received.append((source, factor))
            return source * factor

        source >> multiply

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED
    assert received == [(2, 10)]


@pytest.mark.asyncio
async def test_generic_type_annotations_are_supported(app: Plombery):
    """Regression test: `issubclass` raises on subscripted generics such as
    `List[int]`, which used to make any annotated task fail."""

    received = []

    app.start()

    with Pipeline(id="annotated") as pipeline:

        @task
        def source():
            return [1, 2, 3]

        @task
        def consume(source: List[int]):
            received.append(source)

        source >> consume

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED
    assert received == [[1, 2, 3]]
