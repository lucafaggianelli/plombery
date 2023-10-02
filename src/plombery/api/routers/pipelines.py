from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from plombery.orchestrator import orchestrator
from plombery.api.authentication import NeedsAuth
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
