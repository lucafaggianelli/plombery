from fastapi import APIRouter, HTTPException, Query, Response

from plombery.api.authentication import NeedsAuth
from plombery.database.repository import (
    get_pipeline_run,
    get_task_run_output_by_id,
    list_pipeline_runs,
)
from plombery.database.schemas import PipelineRun, PipelineRunWithTaskRuns
from plombery.exceptions import InvalidDataPath
from plombery.orchestrator.data_storage import read_logs_file
from plombery.schemas import TaskOutputData


class JSONLResponse(Response):
    media_type = "application/jsonl"


router = APIRouter(
    prefix="/runs",
    tags=["Runs"],
    dependencies=[NeedsAuth],
)


DEFAULT_PAGE_SIZE = 30

MAX_PAGE_SIZE = 100


@router.get(
    "/",
    description=(
        "List the runs of a pipeline or of one of its triggers, newest first. "
        "Pages are walked by passing the id of the last run received as "
        "`before_id`; a page shorter than `limit` is the last one."
    ),
)
def list_runs(
    pipeline_id: str | None = None,
    trigger_id: str | None = None,
    limit: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="How many runs to return",
    ),
    before_id: int | None = Query(
        None,
        description="Return only the runs older than this run id",
    ),
) -> list[PipelineRun]:
    return [
        PipelineRun.model_validate(run)
        for run in list_pipeline_runs(
            pipeline_id=pipeline_id,
            trigger_id=trigger_id,
            limit=limit,
            before_id=before_id,
        )
    ]


@router.get("/{run_id}", description="Get a single run with its task runs")
def get_run(run_id: int) -> PipelineRunWithTaskRuns:
    if not (pipeline_run := get_pipeline_run(run_id)):
        raise HTTPException(404, f"The pipeline run {run_id} doesn't exist")

    return PipelineRunWithTaskRuns.model_validate(pipeline_run)


@router.get(
    "/{run_id}/logs",
    response_class=JSONLResponse,
    description="Get the logs of a run, in JSONL format",
)
def get_run_logs(run_id: int) -> Response:
    try:
        logs = read_logs_file(run_id)
    except InvalidDataPath:
        raise HTTPException(status_code=400, detail="Invalid run ID")

    return JSONLResponse(content=logs)


@router.get(
    "/{run_id}/data/{task_run_id}", description="Get the output data of a task run"
)
def get_run_data(task_run_id: str) -> TaskOutputData:
    if not (output := get_task_run_output_by_id(task_run_id)):
        raise HTTPException(404, f"The task run {task_run_id} has no output data")

    return TaskOutputData.model_validate(output)
