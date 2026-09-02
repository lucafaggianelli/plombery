from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError

from plombery.api.authentication import NeedsAuth
from plombery.database.schemas import PipelineRun
from plombery.orchestrator import orchestrator, run_pipeline_now
from plombery.pipeline.pipeline import Pipeline

router = APIRouter(prefix="/pipelines", tags=["Pipelines"], dependencies=[NeedsAuth])


def _populate_next_fire_time(pipeline: Pipeline) -> None:
    for trigger in pipeline.triggers:
        if not trigger.schedule:
            continue

        if job := orchestrator.get_job(pipeline.id, trigger.id):
            trigger.next_fire_time = job.next_run_time


@router.get("/", description="List all the registered pipelines")
def list_pipelines() -> list[Pipeline]:
    pipelines = list(orchestrator.pipelines.values())

    for pipeline in pipelines:
        _populate_next_fire_time(pipeline)

    return pipelines


@router.get("/{pipeline_id}", description="Get a single pipeline")
def get_pipeline(pipeline_id: str) -> Pipeline:
    if not (pipeline := orchestrator.get_pipeline(pipeline_id)):
        raise HTTPException(404, f"The pipeline with ID {pipeline_id} doesn't exist")

    _populate_next_fire_time(pipeline)

    return pipeline


@router.get(
    "/{pipeline_id}/input-schema",
    description="Get the JSON schema of the input parameters for a pipeline",
)
def get_pipeline_input_schema(pipeline_id: str) -> dict[str, Any]:
    if not (pipeline := orchestrator.get_pipeline(pipeline_id)):
        raise HTTPException(404, f"The pipeline with ID {pipeline_id} doesn't exist")

    return pipeline.params.model_json_schema() if pipeline.params else {}


class PipelineRunInput(BaseModel):
    trigger_id: str | None = None
    params: dict[str, Any] | None = None
    reason: str = "api"


@router.post("/{pipeline_id}/run", description="Trigger a pipeline run")
async def run_pipeline(pipeline_id: str, body: PipelineRunInput) -> PipelineRun:
    if not (pipeline := orchestrator.get_pipeline(pipeline_id)):
        raise HTTPException(404, f"The pipeline with ID {pipeline_id} doesn't exist")

    if body.trigger_id:
        triggers = [
            trigger for trigger in pipeline.triggers if trigger.id == body.trigger_id
        ]

        if len(triggers) == 0:
            raise HTTPException(
                status_code=404, detail=f"Trigger {body.trigger_id} not found"
            )

        trigger = triggers[0]

        return await run_pipeline_now(pipeline, trigger=trigger, reason=body.reason)
    else:
        if pipeline.params:
            try:
                pipeline.params.model_validate(body.params)
            except ValidationError as exc:
                raise HTTPException(
                    status_code=422,
                    detail=exc.errors(),
                )

        return await run_pipeline_now(
            pipeline,
            params=body.params,
            reason=body.reason,
        )
