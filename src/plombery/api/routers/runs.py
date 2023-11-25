from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError

from plombery.api.authentication import NeedsAuth
from plombery.database.schemas import PipelineRun
from plombery.exceptions import InvalidDataPath
from plombery.orchestrator import orchestrator, run_pipeline_now
from plombery.orchestrator.data_storage import get_task_run_data_file, read_logs_file
from plombery.database.repository import list_pipeline_runs, get_pipeline_run


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
) -> List[PipelineRun]:
    return list_pipeline_runs(pipeline_id=pipeline_id, trigger_id=trigger_id)


@router.get("/{run_id}")
def get_run(run_id: int) -> PipelineRun:
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


@router.get("/{run_id}/data/{task}")
def get_run_data(run_id: int, task: str):
    try:
        data_file = get_task_run_data_file(run_id, task)
    except InvalidDataPath:
        raise HTTPException(status_code=400, detail="Invalid run or task ID")

    if not data_file.exists():
        raise HTTPException(status_code=404, detail="Task has no data")

    return FileResponse(path=data_file, filename=f"run-{run_id}-{task}-data.json")


class PipelineRunInput(BaseModel):
    pipeline_id: str
    trigger_id: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


@router.post("/")
async def run_pipeline(body: PipelineRunInput) -> PipelineRun:
    if not (pipeline := orchestrator.get_pipeline(body.pipeline_id)):
        raise HTTPException(
            404, f"The pipeline with ID {body.pipeline_id} doesn't exist"
        )

    if body.trigger_id:
        triggers = [
            trigger for trigger in pipeline.triggers if trigger.id == body.trigger_id
        ]

        if len(triggers) == 0:
            raise HTTPException(
                status_code=404, detail=f"Trigger {body.trigger_id} not found"
            )

        trigger = triggers[0]

        return await run_pipeline_now(pipeline, trigger)
    else:
        if pipeline.params:
            try:
                pipeline.params.model_validate(body.params)
            except ValidationError as exc:
                raise HTTPException(
                    status_code=422,
                    detail=exc.errors(),
                )

        return await run_pipeline_now(pipeline, params=body.params)
