"""Tests that a run always reaches a final status.

A run stuck in RUNNING is the worst failure mode of the orchestrator: the UI
shows it as still going, the next scheduled run may be skipped, and nothing
ever recovers it. These cover the paths that used to hang.
"""

import pytest
from pydantic import BaseModel

from plombery import Pipeline, task, _Plombery as Plombery
from plombery.orchestrator import run_pipeline_now
from plombery.pipeline.tasks import MappingMode
from plombery.schemas import FINISHED_STATUS, PipelineRunStatus

from .conftest import wait_for_run


class RequiredParams(BaseModel):
    required_value: int


@pytest.mark.asyncio
async def test_two_skipped_branches_do_not_hang_the_run(app: Plombery):
    """Two mapped tasks skipped in the same completion event.

    Regression test: the skipped set accumulated across iterations while being
    appended to a list, so the same IDs were counted more than once. The
    finished count overshot the number of tasks and, since the check was an
    equality, it never matched and the run stayed RUNNING forever.
    """

    app.start()

    with Pipeline(id="double-skip") as pipeline:

        @task
        def source():
            # Empty, so both fan-outs downstream are skipped
            return []

        @task(mapping_mode=MappingMode.FAN_OUT, map_upstream_id="source")
        def each_a(source):
            return source

        @task(mapping_mode=MappingMode.FAN_OUT, map_upstream_id="source")
        def each_b(source):
            return source

        @task
        def after_a(each_a):
            return "a"

        @task
        def after_b(each_b):
            return "b"

        source >> [each_a, each_b]
        each_a >> after_a
        each_b >> after_b

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id, timeout=5)

    assert run.status == PipelineRunStatus.COMPLETED


@pytest.mark.asyncio
async def test_fan_out_over_an_empty_collection_completes(app: Plombery):
    app.start()

    with Pipeline(id="empty-fan-out") as pipeline:

        @task
        def source():
            return []

        @task(mapping_mode=MappingMode.FAN_OUT, map_upstream_id="source")
        def each(source):
            return source

        source >> each

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id, timeout=5)

    assert run.status == PipelineRunStatus.COMPLETED


@pytest.mark.asyncio
async def test_pipeline_with_no_tasks_completes(app: Plombery):
    """Regression test: with nothing to schedule no task ever reported a
    completion, so the run had no way of ever being closed."""

    app.start()

    pipeline = Pipeline(id="empty-pipeline", tasks=[])
    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id, timeout=5)

    assert run.status == PipelineRunStatus.COMPLETED


@pytest.mark.asyncio
async def test_invalid_input_params_fail_the_run(app: Plombery):
    """Regression test: the input params were validated outside the try block,
    so a ValidationError escaped before the code that advances the DAG."""

    app.start()

    with Pipeline(id="invalid-params", params=RequiredParams) as pipeline:

        @task
        def only_task(params):
            return params.required_value

    app.register_pipeline(pipeline)

    # The model requires a value and none is supplied
    run = await wait_for_run((await run_pipeline_now(pipeline)).id, timeout=5)

    assert run.status == PipelineRunStatus.FAILED


@pytest.mark.asyncio
async def test_task_returning_none_still_advances_the_dag(app: Plombery):
    app.start()

    with Pipeline(id="no-output") as pipeline:

        @task
        def first():
            return None

        @task
        def second(first):
            return None

        first >> second

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id, timeout=5)

    assert run.status in FINISHED_STATUS


@pytest.mark.asyncio
async def test_the_run_records_the_pipeline_version(app: Plombery):
    app.start()

    with Pipeline(id="versioned") as pipeline:

        @task
        def only_task():
            return 1

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id, timeout=5)

    assert run.pipeline_version == pipeline.get_version()


@pytest.mark.asyncio
async def test_an_explicit_version_wins_over_the_computed_one(app: Plombery):
    app.start()

    with Pipeline(id="explicit-version", version="v2.1.0") as pipeline:

        @task
        def only_task():
            return 1

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id, timeout=5)

    assert run.pipeline_version == "v2.1.0"


def test_the_computed_version_tracks_the_shape_of_the_graph():
    """The hash has to change when the graph does, and only then."""

    def build(with_extra_dependency: bool) -> Pipeline:
        pipeline = Pipeline(id="shape")

        with pipeline:

            @task
            def a():
                return 1

            @task
            def b(a):
                return 2

            @task
            def c():
                return 3

            a >> b

            if with_extra_dependency:
                c >> b

        return pipeline

    assert build(False).get_version() == build(False).get_version()
    assert build(False).get_version() != build(True).get_version()
