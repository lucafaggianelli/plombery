"""End to end tests for the DAG execution semantics.

These cover how the orchestrator walks the graph: how data flows between tasks,
how fan-out and fan-in behave, and what happens when something goes wrong.
"""

import asyncio
from typing import List

import pytest

from plombery import Pipeline, task, _Plombery as Plombery
from plombery.database.repository import get_task_run_output_by_id
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


@pytest.mark.asyncio
async def test_wide_fan_in_schedules_the_join_task_once(app: Plombery):
    """Many branches completing at the same time must not schedule the join
    task more than once: every branch reaches `handle_task_completion` and
    checks the very same set of upstream dependencies."""

    app.start()

    with Pipeline(id="wide-fan-in") as pipeline:

        @task
        def start():
            return 1

        branches = []

        for index in range(8):

            @task(id=f"branch_{index}")
            async def branch(start):
                await asyncio.sleep(0.02)
                return "done"

            branches.append(branch)

        @task
        def join(**kwargs):
            return "joined"

        start >> branches

        for branch_task in branches:
            branch_task >> join

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED
    assert count_task_runs(run)["join"] == 1


@pytest.mark.asyncio
async def test_fan_in_schedules_the_join_once_when_emit_yields(
    app: Plombery, monkeypatch: pytest.MonkeyPatch
):
    """A fan-in must run once even when the websocket emit yields to the loop.

    `handle_task_completion` emits before it checks whether the downstream
    task's dependencies are all met. With a real client connected that emit
    suspends, so several branches can each observe "everything upstream is
    done" and each schedule the join. In the test suite nothing is connected
    and the emit never yields, which is why the other fan-in tests cannot see
    this: the yield has to be forced.
    """

    from plombery import websocket

    original_emit = websocket.sio.emit

    async def yielding_emit(*args, **kwargs):
        await asyncio.sleep(0)
        return await original_emit(*args, **kwargs)

    monkeypatch.setattr(websocket.sio, "emit", yielding_emit)

    app.start()

    with Pipeline(id="racing_fan_in") as pipeline:

        @task
        def start():
            return 1

        branches = []

        for index in range(8):

            @task(id=f"branch_{index}")
            async def branch(start):
                await asyncio.sleep(0.02)
                return "done"

            branches.append(branch)

        @task
        def join(**kwargs):
            return "joined"

        start >> branches

        for branch_task in branches:
            branch_task >> join

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED
    assert count_task_runs(run)["join"] == 1


@pytest.mark.asyncio
async def test_a_task_can_return_a_dataframe(app: Plombery):
    """Returning a pandas DataFrame is a documented pattern and must be stored.

    Task outputs used to be written to disk by `store_task_output`, which
    special cased DataFrames; now they go to the database, and a generic
    `__dict__` fallback turned a DataFrame into pandas' internals, which are
    not JSON serializable, so the whole run failed.
    """

    pandas = pytest.importorskip("pandas")

    records = [{"sku": 1, "price": 10}, {"sku": 2, "price": 20}]

    app.start()

    with Pipeline(id="dataframe_output") as pipeline:

        @task
        def produce():
            return pandas.DataFrame(records)

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED

    task_run = run.task_runs[0]
    assert task_run.task_output_id

    output = get_task_run_output_by_id(task_run.task_output_id)
    assert output.data == records


def _files_pipeline(parsed: list, stored: list, fail_fast: bool = True) -> Pipeline:
    """Fan out over four files, one of which is corrupt, then store each one."""

    with Pipeline(id="files", fail_fast=fail_fast) as pipeline:

        @task
        def source():
            return [1, 2, 3, 4]

        @task(mapping_mode=MappingMode.FAN_OUT, map_upstream_id="source")
        async def parse(source):
            # Staggered so the failure lands while the siblings are in flight
            await asyncio.sleep(0.01 * source)

            if source == 2:
                raise ValueError("file 2 is corrupt")

            parsed.append(source)
            return source

        @task(mapping_mode=MappingMode.CHAINED_FAN_OUT, map_upstream_id="parse")
        def store(parse):
            stored.append(parse)

        source >> parse >> store

    return pipeline


def _statuses(run, task_id: str) -> dict:
    """Status of every instance of a task, keyed by map index."""

    return {
        task_run.map_index: task_run.status
        for task_run in run.task_runs
        if task_run.task_id == task_id
    }


@pytest.mark.asyncio
async def test_fan_out_failure_records_the_tasks_that_never_ran(app: Plombery):
    """A failed branch must leave a cancelled task run, not a hole.

    Marking the run FAILED as soon as one instance fails made every other
    in-flight completion bail out, so the tasks downstream of the branches that
    were still running were never scheduled and never recorded: the run showed
    nothing at all for them, which is indistinguishable from a task that was
    never part of the graph.
    """

    parsed, stored = [], []

    pipeline = _files_pipeline(parsed, stored)

    app.start()
    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.FAILED

    # Three files parsed successfully, and their side effects happened
    assert sorted(parsed) == [1, 3, 4]
    assert _statuses(run, "parse") == {
        0: PipelineRunStatus.COMPLETED,
        1: PipelineRunStatus.FAILED,
        2: PipelineRunStatus.COMPLETED,
        3: PipelineRunStatus.COMPLETED,
    }

    # Every instance of the downstream task is accounted for: the ones that did
    # not run say so, instead of being missing altogether
    assert _statuses(run, "store") == {
        0: PipelineRunStatus.COMPLETED,
        1: PipelineRunStatus.CANCELLED,
        2: PipelineRunStatus.CANCELLED,
        3: PipelineRunStatus.CANCELLED,
    }


@pytest.mark.asyncio
async def test_fan_out_without_fail_fast_finishes_the_healthy_branches(
    app: Plombery,
):
    """With `fail_fast=False` only the failed branch is dropped.

    The branches of a fan-out over independent items — one per file, per
    record — have nothing to do with each other, so one corrupt file must not
    abandon work that had already succeeded halfway through.
    """

    parsed, stored = [], []

    pipeline = _files_pipeline(parsed, stored, fail_fast=False)

    app.start()
    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    # The run still fails: a file was not imported
    assert run.status == PipelineRunStatus.FAILED

    # ...but everything that parsed also got stored, no silent gap
    assert sorted(parsed) == [1, 3, 4]
    assert sorted(stored) == [1, 3, 4]

    assert _statuses(run, "store") == {
        0: PipelineRunStatus.COMPLETED,
        1: PipelineRunStatus.CANCELLED,
        2: PipelineRunStatus.COMPLETED,
        3: PipelineRunStatus.COMPLETED,
    }


@pytest.mark.asyncio
async def test_register_pipeline_accepts_a_built_pipeline(app: Plombery):
    """`register_pipeline` must accept a `Pipeline` built with the context manager.

    Without this, a user who builds a pipeline with `with Pipeline()` and then
    calls the flat `register_pipeline(id=..., tasks=[...])` on it hits a
    TypeError, and the natural workaround is to redeclare the whole task list
    by hand, duplicating what `>>` already expressed.
    """

    from plombery import register_pipeline
    from plombery.orchestrator import orchestrator

    app.start()

    with Pipeline(id="via_register_pipeline") as pipeline:

        @task
        def start():
            return 1

        @task
        def finish(start):
            return start + 1

        start >> finish

    returned = register_pipeline(pipeline)

    assert returned is pipeline
    assert orchestrator.pipelines["via_register_pipeline"] is pipeline

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)
    assert run.status == PipelineRunStatus.COMPLETED


@pytest.mark.asyncio
async def test_tasks_defined_outside_the_context_are_registered_by_wiring(
    app: Plombery,
):
    """A task defined outside `with Pipeline()` must join it once wired with `>>`.

    `add_task_to_pipeline` only fires when a `@task` is created, which for a
    task defined at module level happens with no pipeline context active, so
    it's never added anywhere. Wiring it with `>>` inside the block used to be
    silently unable to fix that: `pipeline.tasks` stayed empty even though the
    upstream/downstream ids were set correctly.
    """

    app.start()

    @task
    def extract():
        return [1, 2, 3]

    @task
    def transform(extract):
        return [v * 2 for v in extract]

    with Pipeline(id="outside_context") as pipeline:
        extract >> transform

    assert {t.id for t in pipeline.tasks} == {"extract", "transform"}

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)
    assert run.status == PipelineRunStatus.COMPLETED


@pytest.mark.asyncio
async def test_output_of_binds_by_reference_not_by_name(app: Plombery):
    """`OutputOf` resolves the right upstream task regardless of the argument's name."""

    from plombery import OutputOf

    app.start()

    with Pipeline(id="output_of_run") as pipeline:

        @task
        def fetch_data():
            return [1, 2, 3]

        @task
        def process(data=OutputOf(fetch_data)):
            return sum(data)

        fetch_data >> process

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED

    process_run = next(tr for tr in run.task_runs if tr.task_id == "process")
    output = get_task_run_output_by_id(process_run.task_output_id)
    assert output.data == 6


def test_output_of_without_a_declared_dependency_is_rejected():
    """`OutputOf` only binds data; the edge must still be declared with `>>`.

    Deriving the graph from the signature was explicitly ruled out (too many
    edge cases, and it would make a pure refactor of a function's arguments
    silently change the DAG's topology), so a mismatch between the two must
    be a hard error, not a silently working accident.
    """

    with pytest.raises(ValueError, match="OutputOf.*no declared dependency"):
        with Pipeline(id="output_of_missing_edge"):
            from plombery import OutputOf

            @task
            def fetch_data():
                return [1, 2, 3]

            @task
            def process(data=OutputOf(fetch_data)):
                return sum(data)

            # No `fetch_data >> process` here on purpose.


@pytest.mark.asyncio
async def test_a_task_can_be_reused_across_pipelines(app: Plombery):
    """Wiring the same `Task` object into two pipelines must not leak edges.

    Edges used to be mutated directly onto the `Task` object by `>>`, so
    wiring an already-defined task into a second pipeline changed what the
    first pipeline saw as its own dependencies too, corrupting scheduling
    decisions for a run that had nothing to do with the second pipeline.
    """

    app.start()

    @task
    def shared():
        return 1

    with Pipeline(id="reuse_a") as pipeline_a:

        @task
        def only_in_a(shared):
            return shared + 10

        shared >> only_in_a

    with Pipeline(id="reuse_b") as pipeline_b:

        @task
        def only_in_b(shared):
            return shared + 100

        shared >> only_in_b

    # Each pipeline must see only its own edge for the shared task.
    assert pipeline_a.downstream_of("shared") == {"only_in_a"}
    assert pipeline_b.downstream_of("shared") == {"only_in_b"}

    app.register_pipeline(pipeline_a)
    app.register_pipeline(pipeline_b)

    run_a = await wait_for_run((await run_pipeline_now(pipeline_a)).id)
    run_b = await wait_for_run((await run_pipeline_now(pipeline_b)).id)

    assert run_a.status == PipelineRunStatus.COMPLETED
    assert run_b.status == PipelineRunStatus.COMPLETED

    # Neither run has a task run for the other pipeline's exclusive task.
    assert {tr.task_id for tr in run_a.task_runs} == {"shared", "only_in_a"}
    assert {tr.task_id for tr in run_b.task_runs} == {"shared", "only_in_b"}


@pytest.mark.asyncio
async def test_a_pipeline_registers_itself_when_its_block_ends(app: Plombery):
    """A `with Pipeline()` block registers the pipeline on exit, so importing
    the module that defines it is enough — no explicit `register_pipeline`."""

    from plombery.orchestrator import orchestrator

    app.start()

    with Pipeline(id="self_registered") as pipeline:

        @task
        def only_task():
            return 1

    # No register_pipeline call here on purpose.
    assert orchestrator.pipelines.get("self_registered") is pipeline

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)
    assert run.status == PipelineRunStatus.COMPLETED


@pytest.mark.asyncio
async def test_auto_register_false_leaves_the_pipeline_unregistered(app: Plombery):
    from plombery.orchestrator import orchestrator

    app.start()

    with Pipeline(id="not_registered", auto_register=False) as pipeline:

        @task
        def only_task():
            return 1

    assert "not_registered" not in orchestrator.pipelines

    # It can still be registered explicitly afterwards.
    app.register_pipeline(pipeline)
    assert orchestrator.pipelines.get("not_registered") is pipeline
