from apscheduler.triggers.interval import IntervalTrigger
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
import pytest

from plombery import Pipeline, Trigger, task, _Plombery as Plombery
from plombery.api import app
from plombery.api.routers.runs import get_run_data
from plombery.database.schemas import PipelineRunWithTaskRuns
from plombery.orchestrator import run_pipeline_now
from plombery.pipeline.tasks import MappingMode
from .conftest import wait_for_run
from .pipeline_1 import pipeline1, pipeline1_serialized


client = TestClient(app)


@pytest.mark.asyncio
async def test_api_list_pipelines(app: Plombery):
    app.register_pipeline(pipeline1)

    response = client.get("/api/pipelines/")

    assert response.status_code == 200
    assert response.json() == [pipeline1_serialized]


@pytest.mark.asyncio
async def test_api_list_pipelines_with_auth(with_auth, authenticated, app: Plombery):
    app.register_pipeline(pipeline1)

    response = client.get("/api/pipelines/")

    assert response.status_code == 200
    assert response.json() == [pipeline1_serialized]


@pytest.mark.asyncio
async def test_api_get_pipeline(app: Plombery):
    app.register_pipeline(pipeline1)

    response = client.get("/api/pipelines/pipeline1")

    assert response.status_code == 200
    assert response.json() == pipeline1_serialized


@pytest.mark.asyncio
async def test_api_get_pipeline_with_auth(with_auth, authenticated, app: Plombery):
    app.register_pipeline(pipeline1)

    response = client.get("/api/pipelines/pipeline1")

    assert response.status_code == 200
    assert response.json() == pipeline1_serialized


@pytest.mark.asyncio
async def test_api_get_pipeline_not_existing(app: Plombery):
    app.register_pipeline(pipeline1)

    response = client.get("/api/pipelines/not-existing")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "The pipeline with ID not-existing doesn't exist"
    }


@pytest.mark.asyncio
@pytest.mark.skip
async def test_api_with_auth_when_not_authenticated(with_auth, app: Plombery):
    NOT_AUTH_MSG = {"detail": "You must be authenticated to access this API route"}

    response = client.get("/api/pipelines")
    assert response.status_code == 401
    assert response.json() == NOT_AUTH_MSG

    response = client.get("/api/pipelines/pipeid")
    assert response.status_code == 401
    assert response.json() == NOT_AUTH_MSG


@pytest.mark.asyncio
async def test_run_serializes_an_index_only_for_mapped_task_runs(app: Plombery):
    """`map_index` tells a fan out instance from a plain task run.

    The UI has nothing else to go by: a fan out over a single item produces
    exactly one task run, so the number of runs cannot be used. A plain task
    must therefore serialize a null index, never 0.

    This asserts on the response model rather than on a request, as the API
    runs in another thread and the test database lives in memory, one per
    thread.
    """

    app.start()

    with Pipeline(id="mapping") as pipeline:

        @task
        def plain():
            return ["a", "b"]

        @task(mapping_mode=MappingMode.FAN_OUT, map_upstream_id="plain")
        def mapped(plain):
            return plain.upper()

        plain >> mapped

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    serialized = PipelineRunWithTaskRuns.model_validate(run).model_dump(mode="json")

    indexes = {"plain": [], "mapped": []}

    for task_run in serialized["task_runs"]:
        indexes[task_run["task_id"]].append(task_run["map_index"])

    assert indexes["plain"] == [None]
    assert sorted(indexes["mapped"]) == [0, 1]


@pytest.mark.asyncio
async def test_api_serializes_the_params_of_a_trigger(app: Plombery):
    """A trigger's params are serialized with the model the pipeline declared.

    `Trigger.params` is annotated as a bare `BaseModel`, so without
    `SerializeAsAny` pydantic serializes it with the base class' serializer and
    every trigger answers an empty object, whatever it was configured with.
    """

    class Params(BaseModel):
        n: int = 0
        label: str = ""

    # The scheduler has to be running before the trigger's job is added, as the
    # route reads the job's next fire time and APScheduler only computes it
    # once the job leaves the pending queue.
    app.start()

    with Pipeline(
        id="with_trigger",
        params=Params,
        triggers=[
            Trigger(
                id="hourly",
                name="Hourly",
                schedule=IntervalTrigger(hours=1),
                params=Params(n=7, label="from-trigger"),
            )
        ],
    ) as pipeline:

        @task
        def noop(): ...

    app.register_pipeline(pipeline)

    response = client.get("/api/pipelines/with_trigger")

    assert response.status_code == 200

    trigger = response.json()["triggers"][0]
    assert trigger["params"] == {"n": 7, "label": "from-trigger"}
    assert trigger["schedule"] == "interval[1:00:00]"


@pytest.mark.asyncio
async def test_api_get_run_data_of_a_task_without_output(app: Plombery):
    """A task run with no stored output is a 404, not a 200 with a null body:
    the UI tells the two apart to show "The task has no data".

    This calls the route directly rather than over HTTP, as the API runs in
    another thread and the test database lives in memory, one per thread.
    """

    with pytest.raises(HTTPException) as exc_info:
        get_run_data("not-an-output")

    assert exc_info.value.status_code == 404
