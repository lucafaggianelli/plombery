from typing import Optional, Sequence

from fastapi import APIRouter, HTTPException, Response

from plombery.api.authentication import NeedsAuth
from plombery.database.schemas import PipelineRun, PipelineRunWithTaskRuns
from plombery.exceptions import InvalidDataPath
from plombery.orchestrator.data_storage import read_logs_file
from plombery.database.repository import (
    get_task_run_output_by_id,
    list_pipeline_runs,
    get_pipeline_run,
)


class JSONLResponse(Response):
    media_type = "application/jsonl"


router = APIRouter(
    prefix="/runs",
    tags=["Runs"],
    dependencies=[NeedsAuth],
)


@router.get("/")
def list_runs(
    pipeline_id: Optional[str] = None,
    trigger_id: Optional[str] = None,
) -> Sequence[PipelineRun]:
    return list_pipeline_runs(pipeline_id=pipeline_id, trigger_id=trigger_id)


@router.get("/{run_id}")
def get_run(run_id: int) -> PipelineRunWithTaskRuns:
    if not (pipeline_run := get_pipeline_run(run_id)):
        raise HTTPException(404, f"The pipeline run {run_id} doesn't exist")

    return pipeline_run


@router.get("/{run_id}/logs", response_class=JSONLResponse)
def get_run_logs(run_id: int):
    try:
        logs = read_logs_file(run_id)
    except InvalidDataPath:
        raise HTTPException(status_code=400, detail="Invalid run ID")

    return Response(content=logs, media_type="application/jsonl")


@router.get("/{run_id}/data/{task_run_id}")
def get_run_data(task_run_id: str):
    return get_task_run_output_by_id(task_run_id)
