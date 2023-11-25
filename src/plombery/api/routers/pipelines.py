from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ValidationError

from plombery.api.authentication import NeedsAuth
from plombery.database.schemas import PipelineRun
from plombery.orchestrator import orchestrator, run_pipeline_now
from plombery.pipeline.pipeline import Pipeline
from plombery.pipeline.trigger import Trigger


router = APIRouter(prefix="/pipelines", tags=["Pipelines"], dependencies=[NeedsAuth])


def _populate_next_fire_time(pipeline: Pipeline) -> None:
    for trigger in pipeline.triggers:
        if not trigger.schedule:
            continue

        if job := orchestrator.get_job(pipeline.id, trigger.id):
            trigger.next_fire_time = job.next_run_time


@router.get("/", response_model=None, description="List all the registered pipelines")
def list_pipelines():
    pipelines = list(orchestrator.pipelines.values())

    for pipeline in pipelines:
        _populate_next_fire_time(pipeline)

    return jsonable_encoder(
        pipelines,
        custom_encoder=Trigger.Config.json_encoders,
    )


@router.get("/{pipeline_id}", response_model=None, description="Get a single pipeline")
def get_pipeline(pipeline_id: str):
    if not (pipeline := orchestrator.get_pipeline(pipeline_id)):
        raise HTTPException(404, f"The pipeline with ID {pipeline_id} doesn't exist")

    _populate_next_fire_time(pipeline)

    return jsonable_encoder(pipeline, custom_encoder=Trigger.Config.json_encoders)


@router.get(
    "/{pipeline_id}/input-schema",
    description="Get the JSON schema of the input parameters for a pipeline",
)
def get_pipeline_input_schema(pipeline_id: str):
    if not (pipeline := orchestrator.get_pipeline(pipeline_id)):
        raise HTTPException(404, f"The pipeline with ID {pipeline_id} doesn't exist")

    return pipeline.params.model_json_schema() if pipeline.params else dict()


class PipelineRunInput(BaseModel):
    trigger_id: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


@router.post("/{pipeline_id}/run")
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
