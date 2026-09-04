"""Tests for the pagination of the runs list."""

import pytest
from fastapi.testclient import TestClient

from plombery import _Plombery as Plombery
from plombery.api import app
from plombery.api.routers.runs import MAX_PAGE_SIZE, list_runs
from plombery.database.repository import create_pipeline_run, list_pipeline_runs
from plombery.database.schemas import PipelineRunCreate
from plombery.schemas import PipelineRunStatus
from plombery.utils import utcnow


client = TestClient(app)


def make_runs(count: int, pipeline_id="a-pipeline", trigger_id="_manual") -> list[int]:
    """Create `count` runs and return their ids, oldest first."""

    return [
        create_pipeline_run(
            PipelineRunCreate(
                pipeline_id=pipeline_id,
                trigger_id=trigger_id,
                status=PipelineRunStatus.COMPLETED,
                start_time=utcnow(),
            )
        ).id
        for _ in range(count)
    ]


@pytest.mark.asyncio
async def test_a_page_holds_the_newest_runs(app: Plombery):
    ids = make_runs(5)

    page = list_pipeline_runs(limit=2)

    assert [run.id for run in page] == list(reversed(ids))[:2]


@pytest.mark.asyncio
async def test_the_cursor_walks_back_to_the_oldest_run(app: Plombery):
    ids = make_runs(5)
    newest_first = list(reversed(ids))

    seen = []
    cursor = None

    while True:
        page = list_pipeline_runs(limit=2, before_id=cursor)

        if not page:
            break

        seen.extend(run.id for run in page)
        cursor = page[-1].id

    assert seen == newest_first


@pytest.mark.asyncio
async def test_a_run_created_while_paging_doesnt_shift_the_next_page(app: Plombery):
    """The cursor is an id, not an offset.

    A run starting while the user scrolls the list must not push the runs of
    the following pages around: with an offset, the run at the boundary would
    come back a second time on the next page.
    """

    ids = make_runs(4)

    first_page = list_pipeline_runs(limit=2)

    make_runs(1)

    second_page = list_pipeline_runs(limit=2, before_id=first_page[-1].id)

    assert [run.id for run in first_page] == [ids[3], ids[2]]
    assert [run.id for run in second_page] == [ids[1], ids[0]]


@pytest.mark.asyncio
async def test_a_page_keeps_the_pipeline_and_trigger_filters(app: Plombery):
    mine = make_runs(3, pipeline_id="mine", trigger_id="hourly")
    make_runs(3, pipeline_id="other", trigger_id="hourly")
    make_runs(3, pipeline_id="mine", trigger_id="daily")

    page = list_pipeline_runs(
        pipeline_id="mine", trigger_id="hourly", limit=2, before_id=mine[2]
    )

    assert [run.id for run in page] == [mine[1], mine[0]]


@pytest.mark.asyncio
async def test_the_api_serializes_a_page_of_runs(app: Plombery):
    """This calls the route directly rather than over HTTP, as the API runs in
    another thread and the test database lives in memory, one per thread."""

    ids = make_runs(3)

    page = list_runs(limit=2, before_id=ids[2])

    assert [run.id for run in page] == [ids[1], ids[0]]


@pytest.mark.asyncio
async def test_the_api_rejects_a_page_bigger_than_the_maximum(app: Plombery):
    response = client.get("/api/runs/", params={"limit": MAX_PAGE_SIZE + 1})

    assert response.status_code == 422
